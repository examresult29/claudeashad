/*!
 * BD e-Return calculation engine (JavaScript port of ereturn/calc.py).
 *
 * compute(input, profiles) -> { V, warnings }
 *   input    : taxpayer data (same JSON format as the Python engine)
 *   profiles : { "<profile id>": <rules json>, ... }
 * V holds every figure printed on the 12-page return, keyed like fields.json.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BDERCalc = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var DEFAULT_PROFILE = "ay2026-27";
  var GOVT_ROWS = ["basic_pay", "arrear_pay", "special_allowance", "house_rent_allowance",
    "medical_allowance", "conveyance_allowance", "festival_allowance", "support_staff_allowance",
    "leave_allowance", "honorarium", "overtime_allowance", "baishakhi_allowance", "pf_interest",
    "lamp_grant", "gratuity", "others"];
  var PRIVATE_ROWS = ["basic_pay", "allowances", "advance_salary", "gratuity_pension", "perquisites",
    "in_lieu_of_salary", "employee_share_scheme", "accommodation", "car_benefit", "other_benefits",
    "employer_pf_contribution", "others"];
  var INVEST_ROWS = ["life_insurance", "dps", "govt_securities", "listed_securities", "pf_1925", "rpf",
    "pension_fund", "benevolent_group_insurance", "zakat", "others"];
  var TAXFREE_ROWS = ["govt_pf", "taxed_distribution", "pf_1925_income", "voluntary_retirement",
    "pensioners_savings_certificate", "firm_capital_share", "huf_share", "foreign_remittance",
    "wage_earners_fund", "hill_tracts", "agricultural", "software_it", "handicrafts_export", "sme",
    "zero_coupon", "govt_pension", "welfare_allowance", "govt_award", "briddhashram", "seagoing_ship", "other"];
  var LIFESTYLE_ROWS = ["food_clothing", "housing", "transport", "utility", "education", "travel",
    "festival", "tax_paid", "loan_interest"];
  var CATEGORIES = ["general", "female", "senior", "disabled", "third_gender",
    "war_wounded_freedom_fighter", "july_joddha"];
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function InputError(message) { this.name = "InputError"; this.message = message; }
  InputError.prototype = Object.create(Error.prototype);

  /** Excel ROUND(x, 0): half away from zero. */
  function rnd(x) {
    var a = Math.abs(x);
    var r = Math.floor(a + 0.5 + 1e-9);
    return x < 0 ? -r : r;
  }

  /** Read an amount: numbers, "1,23,456", "" and null. */
  function num(v) {
    if (v === null || v === undefined || v === "") return 0;
    if (typeof v === "number") return isFinite(v) ? v : 0;
    if (typeof v === "boolean") return v ? 1 : 0;
    var s = String(v).replace(/,/g, "").replace(/Tk/gi, "").replace(/৳/g, "").trim();
    if (!s) return 0;
    var n = Number(s);
    if (!isFinite(n)) throw new InputError("'" + v + "' is not an amount.");
    return n;
  }

  /** Like num() but keeps "not given" as null. */
  function opt(v) { return (v === null || v === undefined || v === "") ? null : num(v); }

  function obj(v) { return (v && typeof v === "object" && !Array.isArray(v)) ? v : {}; }
  function str(v) { return (v === null || v === undefined) ? "" : String(v); }
  function fmt(n) { return Math.round(n).toLocaleString("en-US"); }

  function pct(rate) {
    var p = rate * 100;
    if (Math.abs(p - Math.round(p)) < 1e-9) return Math.round(p) + "%";
    return String(Number(p.toPrecision(6))) + "%";
  }

  function digits(s) { return str(s).replace(/\D/g, ""); }

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  /** Accepts YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY. Returns {y, m, d} or null. */
  function parseDate(v) {
    if (!v) return null;
    var s = String(v).trim(), m;
    if ((m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s))) return mk(+m[1], +m[2], +m[3], v);
    if ((m = /^(\d{1,2})[\/.-](\d{1,2})[\/.-](\d{4})$/.exec(s))) return mk(+m[3], +m[2], +m[1], v);
    throw new InputError("Cannot read date '" + v + "'. Use YYYY-MM-DD or DD/MM/YYYY.");
  }
  function mk(y, m, d, raw) {
    var dt = new Date(Date.UTC(y, m - 1, d));
    if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d)
      throw new InputError("Cannot read date '" + raw + "'.");
    return { y: y, m: m, d: d };
  }

  function normAy(v) {
    var m = /^\s*(\d{4})\s*[-\/]\s*(\d{2}|\d{4})\s*$/.exec(str(v));
    if (!m) throw new InputError("Assessment year '" + v + "' should look like 2026-2027.");
    var start = +m[1];
    return { text: start + "-" + (start + 1), start: start };
  }

  function loadRules(profiles, id) {
    var R = profiles[id];
    if (!R) throw new InputError("Unknown tax rules '" + id + "'. Available: " + Object.keys(profiles).join(", "));
    if (R.slabs.length !== 5 || R.slabs[4].width !== null)
      throw new InputError("A rules profile needs exactly 5 slabs after the tax-free band, the last open-ended.");
    return R;
  }

  function sum(arr) { var t = 0; for (var i = 0; i < arr.length; i++) t += arr[i]; return t; }

  function compute(inp, profiles) {
    inp = obj(inp);
    var W = [];
    var V = {};
    var tp = obj(inp.taxpayer), form = obj(inp.form);
    var profile = inp.rules_profile || DEFAULT_PROFILE;
    var R = loadRules(profiles, profile);
    V.rules_profile = profile;
    if (R.warning) W.push("Rules profile '" + profile + "': " + R.warning);

    // ------------------------------------------------------------ identity
    var ay = normAy(inp.assessment_year || "2026-2027");
    var iy = { y: ay.start, m: 6, d: 30 };
    V.ay = ay.text;
    V.iy_end_mdy = iy.m + "/" + iy.d + "/" + iy.y;
    V.iy_end_dmy = iy.d + "-" + MONTHS[iy.m - 1] + "-" + pad2(iy.y % 100);

    var name = str(tp.name).trim();
    if (!name) throw new InputError("Enter the taxpayer's name.");
    V.name = name;
    V.name_line = "Name: " + name;
    var tin = digits(tp.tin);
    if (tin.length !== 12) throw new InputError("The TIN must have 12 digits (got '" + str(tp.tin) + "').");
    V.tin = tin;
    V.nid = str(tp.nid || tp.passport);
    V.circle = str(tp.circle);
    V.zone = str(tp.tax_zone);
    var resident = tp.resident === undefined ? true : !!tp.resident;
    V.resident = resident;
    V.nonresident = !resident;
    var dob = parseDate(tp.dob);
    V.dob_digits = dob ? pad2(dob.d) + pad2(dob.m) + dob.y : "";
    ["spouse_name", "spouse_tin", "address", "telephone", "mobile", "email", "employer",
      "organization", "bin", "partners", "father_or_husband"].forEach(function (k) { V[k] = str(tp[k]); });
    V.relation = str(tp.relation || "father").toLowerCase();
    V.place = str(form.place);
    var signed = parseDate(form.date);
    V.date = signed ? pad2(signed.d) + "/" + pad2(signed.m) + "/" + signed.y : "";
    var docs = form.documents;
    if (docs === undefined || docs === null)
      docs = ["Tax Calculation", "Tax Free Income/ Exempted", "Related Supporting Documents"];
    for (var di = 0; di < 7; di++) V["doc" + (di + 1)] = di < docs.length ? str(docs[di]) : "";
    if (docs.length > 7) W.push("Only 7 documents fit in the list on page 3; the rest were left out.");

    // Special-benefit category -> tax-free threshold.
    var cats = tp.category || ["general"];
    cats = typeof cats === "string" ? [cats] : cats.slice();
    var gender = str(tp.gender).toLowerCase();
    if (gender === "female" && cats.indexOf("female") < 0) cats.push("female");
    if ((gender === "third_gender" || gender === "third gender") && cats.indexOf("third_gender") < 0)
      cats.push("third_gender");
    var age = null;
    if (dob) {
      age = iy.y - dob.y - ((iy.m < dob.m || (iy.m === dob.m && iy.d < dob.d)) ? 1 : 0);
      if (age >= 65 && cats.indexOf("senior") < 0) cats.push("senior");
    }
    cats.forEach(function (c) {
      if (CATEGORIES.indexOf(c) < 0) throw new InputError("Unknown category '" + c + "'.");
    });
    var parent = !!tp.parent_of_disabled;
    var threshold = Math.max.apply(null, cats.map(function (c) { return R.thresholds[c]; }));
    if (parent) threshold += R.thresholds.parent_of_disabled_addition;
    V.threshold = threshold;

    var boxes = form.special_benefit_boxes === undefined ? "auto" : form.special_benefit_boxes;
    if (boxes === "auto") {
      boxes = cats.filter(function (c) { return c !== "general"; });
      if (parent) boxes.push("parent_of_disabled");
    }
    [["war_wounded_freedom_fighter", "box.ff"], ["female", "box.female"], ["third_gender", "box.third"],
      ["disabled", "box.disabled"], ["senior", "box.65"], ["parent_of_disabled", "box.parent"]]
      .forEach(function (b) { V[b[1]] = boxes.indexOf(b[0]) >= 0; });
    if (boxes.indexOf("july_joddha") >= 0) V["box.ff"] = true;

    // -------------------------------------------------- Schedule 1 salary
    var sal = obj(inp.salary), gov = obj(sal.govt);
    var taxable = sal.govt_taxable_items || R.govt_salary_taxable_items;
    var incT = 0, exmT = 0, taxT = 0;
    GOVT_ROWS.forEach(function (k) {
      var a = num(gov[k]);
      V["s1a." + k + ".inc"] = a;
      if (taxable.indexOf(k) >= 0) { V["s1a." + k + ".exm"] = null; V["s1a." + k + ".tax"] = a; taxT += a; }
      else { V["s1a." + k + ".exm"] = a; V["s1a." + k + ".tax"] = null; exmT += a; }
      incT += a;
    });
    V["s1a.inc"] = incT; V["s1a.exm"] = exmT; V["s1a.tax"] = taxT;

    var pri = obj(sal.private), pTotal = 0;
    PRIVATE_ROWS.forEach(function (k) { var a = num(pri[k]); V["s1b." + k] = a; pTotal += a; });
    var ex = R.private_salary_exemption;
    var pExempt = pTotal > 0 ? rnd(Math.min(pTotal * ex.fraction, ex.cap)) : 0;
    if (sal.private_exemption !== undefined && sal.private_exemption !== null && sal.private_exemption !== "")
      pExempt = num(sal.private_exemption);
    V["s1b.sub"] = V["s1b.total"] = pTotal;
    V["s1b.exempt"] = pExempt;
    V["s1b.net"] = pTotal - pExempt;

    // ----------------------------------------- Schedule 2 house property
    var props = inp.house_property || [];
    if (!Array.isArray(props)) props = [props];
    var KEYS = ["r1", "r2", "r3", "r4", "r5", "r6", "da", "db", "dc", "dd", "de", "df", "r8", "r9"];
    var rows = {}; KEYS.forEach(function (k) { rows[k] = 0; });
    var shareIncome = 0, partial = false, rates = [], descs = [];
    props.forEach(function (p) {
      p = obj(p);
      var r1 = num(p.annual_value), r2 = num(p.advance_rent), r3 = num(p.other_benefits);
      var r4 = num(p.adjusted_advance_rent), r5 = num(p.vacancy_allowance);
      var r6 = r1 + r2 + r3 - r4 - r5;
      var kind = str(p.type || "residential").toLowerCase();
      var rate = (p.repair_rate !== undefined && p.repair_rate !== null && p.repair_rate !== "")
        ? num(p.repair_rate) : R.house_repair_rate[kind];
      if (rate === undefined) throw new InputError("House property type '" + kind + "' must be residential or commercial.");
      if (rates.indexOf(rate) < 0) rates.push(rate);
      var da = rnd(r6 * rate);
      var db = num(p.municipal_tax), dc = num(p.land_revenue), dd = num(p.loan_interest);
      var de = num(p.insurance_premium), df = num(p.other_deductions);
      var r8 = da + db + dc + dd + de + df, r9 = r6 - r8;
      var share = p.ownership_share;
      if (share !== undefined && share !== null && share !== "" && Number(share) < 1) {
        partial = true; shareIncome += rnd(r9 * Number(share));
      } else shareIncome += r9;
      var vals = [r1, r2, r3, r4, r5, r6, da, db, dc, dd, de, df, r8, r9];
      KEYS.forEach(function (k, i) { rows[k] += vals[i]; });
      if (p.description) descs.push(str(p.description));
    });
    KEYS.forEach(function (k) { V["s2." + k] = rows[k]; });
    V["s2.r7"] = rows.r8;
    V["s2.r10"] = partial ? shareIncome : null;
    V["s2.rate"] = rates.length === 1 ? pct(rates[0]) : (rates.length ? "Mixed" : pct(R.house_repair_rate.residential));
    V["s2.desc"] = descs.join("; ");
    var houseIncome = props.length ? shareIncome : 0;

    // ------------------------------------------ Schedule 3 agriculture
    var ag = obj(inp.agriculture);
    V["s3.nature"] = str(ag.nature);
    V["s3.r1"] = num(ag.turnover); V["s3.r2"] = num(ag.gross_profit); V["s3.r3"] = num(ag.expenses);
    V["s3.r4"] = V["s3.r2"] - V["s3.r3"];

    // --------------------------------------------- Schedule 4 business
    var bz = obj(inp.business), bs = obj(bz.balance_sheet);
    V["s4.name"] = str(bz.name); V["s4.nature"] = str(bz.nature); V["s4.address"] = str(bz.address);
    V["s4.r1"] = num(bz.turnover); V["s4.r2"] = num(bz.gross_profit);
    V["s4.r3"] = num(bz.expenses); V["s4.r4"] = num(bz.bad_debt);
    V["s4.r5"] = V["s4.r2"] - V["s4.r3"] - V["s4.r4"];
    V["s4.r6"] = num(bs.cash_bank); V["s4.r7"] = num(bs.inventory);
    V["s4.r8"] = num(bs.fixed_assets); V["s4.r9"] = num(bs.other_assets);
    V["s4.r10"] = V["s4.r6"] + V["s4.r7"] + V["s4.r8"] + V["s4.r9"];
    V["s4.r11"] = num(bs.opening_capital); V["s4.r12"] = V["s4.r5"]; V["s4.r13"] = num(bs.drawings);
    V["s4.r14"] = V["s4.r11"] + V["s4.r12"] - V["s4.r13"];
    V["s4.r15"] = num(bs.liabilities);
    V["s4.r16"] = V["s4.r14"] + V["s4.r15"];
    var bizPresent = Object.keys(bs).length > 0;
    if (bizPresent && Math.abs(V["s4.r16"] - V["s4.r10"]) >= 1)
      W.push("Schedule 4 balance sheet does not balance: total assets " + fmt(V["s4.r10"]) +
        " vs capital + liabilities " + fmt(V["s4.r16"]) + ".");

    // -------------------------------------------- total income (1-11)
    var oi = obj(inp.other_income);
    var sanchaya = num(oi.sanchayapatra_interest);
    V.r1 = V["s1a.tax"] + V["s1b.net"];
    V.r2 = houseIncome;
    V.r3 = V["s3.r4"];
    V.r4 = V["s4.r5"];
    V.r5 = num(oi.capital_gains);
    V.r6 = num(oi.financial_assets) + sanchaya;
    V.r7 = num(oi.other_sources);
    V.r8 = num(oi.firm_share);
    V.r9 = num(oi.minor_spouse);
    V.r10 = num(oi.foreign);
    V.r11 = 0; for (var ri = 1; ri <= 10; ri++) V.r11 += V["r" + ri];

    // --------------------------------------------- tax-free income sheet
    var tf = obj(inp.exempt_income);
    V["tf.r01"] = V["s1a.exm"] + V["s1b.exempt"] + num(tf.salary_other);
    TAXFREE_ROWS.forEach(function (k, i) { V["tf.r" + pad2(i + 2)] = num(tf[k]); });
    V["tf.total"] = 0; for (var ti = 1; ti <= 22; ti++) V["tf.total"] += V["tf.r" + pad2(ti)];
    V.r26 = V["tf.total"];

    // ---------------------------------------------- A. slab income
    V["tc.A"] = V.r11;
    V["tc.sp"] = sanchaya;
    var A = V["tc.An"] = V.r11 - sanchaya;

    // ---------------------------------------------------- B. slab tax
    var bands = [[threshold, 0]].concat(R.slabs.map(function (s) { return [s.width, s.rate]; }));
    var rest = Math.max(A, 0), gross = 0;
    bands.forEach(function (b, i) {
      var part = b[0] === null ? rest : Math.min(rest, b[0]);
      rest -= part;
      V["tc.s" + i + ".inc"] = part;
      V["tc.s" + i + ".rate"] = pct(b[1]);
      V["tc.s" + i + ".tax"] = part * b[1];
      gross += part * b[1];
    });
    V["tc.sinc"] = Math.max(A, 0);
    var B = V["tc.B"] = rnd(gross);

    // ------------------------------------------------------- C. rebate
    var inv = obj(inp.investments), totalInv = 0;
    INVEST_ROWS.forEach(function (k, i) { var a = num(inv[k]); V["s5.r" + (i + 1)] = a; totalInv += a; });
    V["s5.r11"] = totalInv;
    var rb = R.rebate;
    V["tc.ci"] = Math.max(A, 0) * rb.income_rate;
    V["tc.cii"] = totalInv * rb.investment_rate;
    V["tc.ciii"] = rb.cap;
    var C = V["tc.C"] = rnd(Math.min(V["tc.ci"], V["tc.cii"], V["tc.ciii"]));
    var tx = obj(inp.tax);
    if (tx.rebate_allowed === false) C = V["tc.C"] = 0;
    V["s5.r12"] = C;
    var cUsed = Math.min(C, B);
    var D = V["tc.D"] = B - cUsed;

    // ------------------------------------------------- E. minimum tax
    var mt = R.minimum_tax, e1;
    if (A <= threshold) e1 = 0;
    else if (mt.mode === "flat") e1 = tp.first_return ? mt.first_return_amount : mt.amount;
    else e1 = mt.locations[tp.location || "other"];
    if (tx.minimum_tax !== undefined && tx.minimum_tax !== null && tx.minimum_tax !== "") e1 = num(tx.minimum_tax);
    V["tc.ei"] = e1; V["tc.eii"] = num(tx.min_tax_163_2kha); V["tc.eiii"] = num(tx.min_tax_163_5ka);
    var E = V["tc.E"] = Math.max(V["tc.ei"], V["tc.eii"], V["tc.eiii"]);
    var F = V["tc.F"] = Math.max(D, E);
    if (E > D && F > 0) W.push("Minimum tax applies: tax after rebate is " + fmt(D) + " but the minimum is " + fmt(E) + ".");

    // ------------------------------------------- payments (J) and wealth
    var pay = obj(inp.payments);
    ["tds_salary", "ait_sanchayapatra", "ait_wppf", "ait_car", "ait_bank_interest", "refund_adjustment",
      "advance_tax"].forEach(function (k, i) { V["tc.j" + (i + 1)] = num(pay[k]); });
    V["tc.jsub1"] = V["tc.j1"] + V["tc.j2"] + V["tc.j3"] + V["tc.j4"] + V["tc.j5"];
    V["tc.jsub2"] = V["tc.j6"] + V["tc.j7"];
    var H = V["tc.H"] = (tx.final_tax !== undefined && tx.final_tax !== null && tx.final_tax !== "")
      ? num(tx.final_tax) : (sanchaya ? V["tc.j2"] : 0);
    var env = num(tx.environmental_surcharge), delay = num(tx.delay_interest);
    var paidGiven = opt(pay.paid_with_return);

    var life = obj(inp.lifestyle), wl = obj(inp.wealth), assets = obj(wl.assets), liab = obj(wl.liabilities);
    var firstReturn = !!tp.first_return;
    var prev = opt(wl.previous_net_wealth);
    var mode = wl.balancing_item || (prev === null ? "gift" : "cash");
    if (["cash", "gift", "none"].indexOf(mode) < 0) throw new InputError("Balancing item must be cash, gift or none.");

    V["a.agg"] = bizPresent ? V["s4.r10"] : num(assets.business_capital_aggregate);
    V["a.bliab"] = bizPresent ? V["s4.r15"] : num(assets.business_liabilities);
    V["a.bcap"] = V["a.agg"] - V["a.bliab"];
    V["a.dir"] = num(assets.director_shareholdings);
    V["a.bcap_other"] = V["a.bcap"];
    var allItems = assets.non_agricultural_property || [], items = allItems;
    if (items.length > 4) {
      var extra = items.slice(3);
      items = items.slice(0, 3).concat([{
        description: "Other " + extra.length + " properties (see annexure)",
        value: sum(extra.map(function (x) { return num(obj(x).value); }))
      }]);
      W.push("More than 4 non-agricultural properties: lines 4+ were merged into one line; attach an annexure.");
    }
    for (var ii = 0; ii < 4; ii++) {
      var it = ii < items.length ? obj(items[ii]) : null;
      V["a.d" + (ii + 1) + "_desc"] = it ? str(it.description) : "";
      V["a.d" + (ii + 1) + "_val"] = it ? num(it.value) : null;
    }
    V["a.d_total"] = sum(allItems.map(function (x) { return num(obj(x).value); }));
    var agri = assets.agricultural_property || [];
    V["a.e_total"] = sum(agri.map(function (x) { return num(obj(x).value); }));
    V["a.e_desc"] = agri.filter(function (x) { return obj(x).description; })
      .map(function (x) { return str(obj(x).description); }).join("; ");
    ["debenture_bond", "sanchayapatra_dps", "life_insurance", "loan_given", "fdr", "provident_fund",
      "other_investment"].forEach(function (k, i) { V["a.f" + (i + 1)] = num(assets[k]); });
    V["a.f_total"] = 0; for (var fi = 1; fi <= 7; fi++) V["a.f_total"] += V["a.f" + fi];
    V["a.g"] = num(assets.motor_car);
    V["a.g_desc"] = str(assets.motor_car_details);
    V["a.h"] = num(assets.ornaments);
    V["a.h_qty"] = str(assets.ornaments_quantity);
    V["a.h_type"] = (assets.ornaments_type !== undefined && assets.ornaments_type !== null) ? str(assets.ornaments_type) : "(Gold)";
    V["a.h_note"] = str(assets.ornaments_note);
    V["a.i"] = num(assets.furniture_electronics);
    V["a.i_note"] = str(assets.furniture_note);
    V["a.j"] = num(assets.other_assets);
    var nonCash = V["a.bcap"] + V["a.dir"] + V["a.d_total"] + V["a.e_total"] + V["a.f_total"] +
      V["a.g"] + V["a.h"] + V["a.i"] + V["a.j"];
    V["w.6a"] = num(liab.institutional); V["w.6b"] = num(liab.non_institutional); V["w.6c"] = num(liab.other);
    V["w.liab"] = V["w.6a"] + V["w.6b"] + V["w.6c"];
    var otherOut = num(wl.other_outflows), giftIn = num(wl.gift_and_other_receipts), cashIn = num(assets.cash_bank);
    var lifeAmounts = {};
    LIFESTYLE_ROWS.forEach(function (k) { if (k !== "tax_paid") lifeAmounts[k] = num(life[k]); });
    var lifeTaxOverride = opt(life.tax_paid);
    var surchargeOverride = opt(tx.net_wealth_surcharge);
    var sc = R.surcharge;

    function surchargeFor(net) {
      if (surchargeOverride !== null) return Math.trunc(surchargeOverride);
      var rate = 0;
      for (var b = 0; b < sc.bands.length; b++) {
        if (sc.bands[b].upto === null || net <= sc.bands[b].upto) { rate = sc.bands[b].rate; break; }
      }
      if (tx.surcharge_trigger && rate < sc.trigger_rate) rate = sc.trigger_rate;
      var base = sc.base === "regular_tax" ? D : F;
      return rnd(base * rate);
    }

    function settle(surcharge) {
      var s = {};
      s.G = surcharge + env + delay;
      s.I = F + s.G + H;
      s.K = s.I - V["tc.jsub1"] - V["tc.jsub2"];
      s.p23 = paidGiven !== null ? paidGiven : Math.max(s.K, 0);
      s.p24 = V["tc.jsub1"] + V["tc.j7"] + V["tc.j6"] + s.p23;
      s.lifeTax = lifeTaxOverride !== null ? lifeTaxOverride : s.p24;
      s.lifeTotal = s.lifeTax;
      for (var k in lifeAmounts) s.lifeTotal += lifeAmounts[k];
      s.expenses = s.lifeTotal + otherOut;
      if (mode === "gift") {
        s.net = nonCash + cashIn - V["w.liab"];
        s.gift = s.net + s.expenses - (prev || 0) - V.r11 - V.r26;
        s.cash = cashIn;
      } else {
        s.gift = giftIn;
        s.net = V.r11 + V.r26 + s.gift + (prev || 0) - s.expenses;
        s.cash = mode === "cash" ? s.net + V["w.liab"] - nonCash : cashIn;
      }
      return s;
    }

    // Net wealth sets the surcharge, and the surcharge (as tax paid, a lifestyle
    // expense) lowers net wealth, so look for a surcharge that agrees with itself.
    var surcharge = 0, seen = [], S = null, converged = false, nw;
    for (var it2 = 0; it2 < 6; it2++) {
      S = settle(surcharge);
      nw = surchargeFor(S.net);
      if (nw === surcharge) { converged = true; break; }
      seen.push(surcharge, nw);
      surcharge = nw;
    }
    if (!converged) {
      surcharge = Math.max.apply(null, seen);
      S = settle(surcharge);
      W.push("Net wealth sits on a surcharge band edge (the surcharge itself moves it across); the higher surcharge was used. Check return line 17.");
    }

    V["tc.gs"] = surcharge + env;
    V["tc.gd"] = delay;
    V["tc.G"] = S.G;
    V["tc.I"] = S.I;
    V["tc.K"] = S.K;
    V["tc.paid"] = paidGiven !== null ? paidGiven : 0;
    V["tc.challan"] = str(pay.challan_number);
    V["tc.net"] = S.K - V["tc.paid"];

    V.r12 = B; V.r13 = cUsed; V.r14 = D; V.r15 = E; V.r16 = F;
    V.r17a = surcharge; V.r17b = env;
    V.r17 = surcharge + env;
    V.r18 = delay + H;
    V.r19 = F + V.r17 + V.r18;
    V.r20 = V["tc.jsub1"]; V.r21 = V["tc.j7"]; V.r22 = V["tc.j6"];
    V.r22_years = str(pay.refund_assessment_years);
    V.r23 = S.p23;
    V.r24 = S.p24;
    V.r25 = V.r19 - S.p24;
    V["ack.income"] = V.r11; V["ack.paid"] = S.p24;
    if (V.r25 > 0) W.push("Deficit of Tk " + fmt(V.r25) + ": payments are less than the tax payable.");
    else if (V.r25 < 0) W.push("Excess payment of Tk " + fmt(-V.r25) + " (refundable).");

    var comments = obj(life.comments);
    LIFESTYLE_ROWS.forEach(function (k, i) {
      V["lb.r" + (i + 1)] = k === "tax_paid" ? S.lifeTax : lifeAmounts[k];
      V["lb.c" + (i + 1)] = str(comments[k]);
    });
    V["lb.total"] = V["lb.total2"] = S.lifeTotal;

    V["w.1a"] = V.r11; V["w.1b"] = V.r26; V["w.1c"] = S.gift;
    V["w.gift_label"] = (wl.gift_label !== undefined && wl.gift_label !== null)
      ? str(wl.gift_label) : (firstReturn ? "(First Return)" : "");
    V["w.src"] = V["w.1a"] + V["w.1b"] + V["w.1c"];
    V["w.2"] = prev;
    V["w.3"] = V["w.src"] + (prev || 0);
    V["w.4a"] = S.lifeTotal; V["w.4b"] = otherOut;
    V["w.exp"] = S.expenses;
    V["w.5"] = V["w.3"] - V["w.exp"];
    V["w.7"] = V["w.5"] + V["w.liab"];
    V["a.k"] = S.cash;
    V["a.total"] = nonCash + S.cash;
    if (mode === "gift" && S.gift < 0)
      W.push("Balancing figure 'Receipt of gift and others' is negative (" + fmt(S.gift) + "): the listed assets " +
        "are smaller than income + previous wealth - expenses. Check the assets or expenses.");
    if (mode === "cash" && S.cash < 0)
      W.push("Balancing figure 'Cash, bank and fund' is negative (" + fmt(S.cash) + "): expenses and assets exceed " +
        "the sources of fund. Add a source (gift, loan) or check the figures.");
    if (Math.abs(V["a.total"] - V["w.7"]) >= 1)
      W.push("IT-10B does not balance: total assets " + fmt(V["a.total"]) + " vs gross wealth " + fmt(V["w.7"]) +
        " (difference " + fmt(V["a.total"] - V["w.7"]) + ").");

    V.age = age;
    V.categories = cats;
    V.balancing_mode = mode;
    return { V: V, warnings: W };
  }

  return {
    compute: compute, InputError: InputError, rnd: rnd, num: num, DEFAULT_PROFILE: DEFAULT_PROFILE,
    GOVT_ROWS: GOVT_ROWS, PRIVATE_ROWS: PRIVATE_ROWS, INVEST_ROWS: INVEST_ROWS,
    TAXFREE_ROWS: TAXFREE_ROWS, LIFESTYLE_ROWS: LIFESTYLE_ROWS
  };
});
