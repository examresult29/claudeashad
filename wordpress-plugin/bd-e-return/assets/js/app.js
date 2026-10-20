/*!
 * BD e-Return data-entry app: form, live tax computation, PDF preview/download/print.
 * Everything runs in the browser; no taxpayer data is sent to the server.
 */
(function () {
  "use strict";

  var CFG = window.BDER_CONFIG || {};
  var PROFILES = CFG.profiles || ["ay2026-27", "sample-template", "fo2025"];
  var STORE_KEY = "bder-draft-v1";
  var DEFAULT_DOCS = ["Tax Calculation", "Tax Free Income/ Exempted", "Related Supporting Documents"];
  var PROFILE_LABELS = {
    "ay2026-27": "AY 2026-27 (Finance Act 2026, as reported)",
    "sample-template": "Sample template (older 5% slab)",
    "fo2025": "Finance Ordinance 2025 (Tk 3.75 lakh)"
  };

  // ------------------------------------------------------------------ form schema
  // t: text | num | optnum | date | select | check | multi | area | lines | pct | boxes
  var SECTIONS = [
    { id: "taxpayer", title: "Taxpayer", note: "Printed on page 1 of the return and on every schedule.", groups: [
      { fields: [
        { p: "taxpayer.name", l: "Name of the assessee", req: true, wide: true },
        { p: "taxpayer.tin", l: "TIN", hint: "12 digits", req: true, im: "numeric" },
        { p: "taxpayer.nid", l: "NID or passport number", im: "numeric" },
        { p: "taxpayer.circle", l: "Circle" },
        { p: "taxpayer.tax_zone", l: "Tax zone" },
        { p: "taxpayer.dob", l: "Date of birth", t: "date" },
        { p: "taxpayer.gender", l: "Gender", t: "select", o: [["male", "Male"], ["female", "Female"], ["third_gender", "Third gender"]] },
        { p: "taxpayer.resident", l: "Resident in Bangladesh", t: "check" },
        { p: "taxpayer.first_return", l: "First return", t: "check", hint: "No IT-10B was filed last year" }
      ] },
      { title: "Special tax-free limit", fields: [
        { p: "taxpayer.category", l: "Also applies", t: "multi", wide: true, o: [
          ["disabled", "Person with disability"], ["war_wounded_freedom_fighter", "Gazetted war-wounded freedom fighter"],
          ["july_joddha", "July Joddha"]] },
        { p: "taxpayer.parent_of_disabled", l: "Parent or guardian of a person with disability", t: "check", wide: true },
        { p: "form.special_benefit_boxes", l: "Tick the matching boxes on page 1", t: "boxes", wide: true,
          hint: "Women and people aged 65 or more are detected from gender and date of birth" }
      ] },
      { title: "Family and contact", fields: [
        { p: "taxpayer.father_or_husband", l: "Father's or husband's name" },
        { p: "taxpayer.relation", l: "That name is the", t: "select", o: [["father", "Father"], ["husband", "Husband"]] },
        { p: "taxpayer.spouse_name", l: "Spouse's name" },
        { p: "taxpayer.spouse_tin", l: "Spouse's TIN", im: "numeric" },
        { p: "taxpayer.address", l: "Address", t: "area", wide: true },
        { p: "taxpayer.telephone", l: "Telephone", im: "tel" },
        { p: "taxpayer.mobile", l: "Mobile", im: "tel" },
        { p: "taxpayer.email", l: "Email", im: "email" },
        { p: "taxpayer.employer", l: "Employer", wide: true },
        { p: "taxpayer.organization", l: "Name of organisation (business)" },
        { p: "taxpayer.bin", l: "Business identification number (BIN)" },
        { p: "taxpayer.partners", l: "Partners and their TINs (firm or AOP)", t: "area", wide: true }
      ] }
    ] },
    { id: "salary", title: "Salary", form: "Schedule 1", sum: "r1", groups: [
      { title: "Government pay scale", fields: [
        ["basic_pay", "Basic pay"], ["arrear_pay", "Arrear pay"], ["special_allowance", "Special allowance"],
        ["house_rent_allowance", "House rent allowance"], ["medical_allowance", "Medical allowance"],
        ["conveyance_allowance", "Conveyance allowance"], ["festival_allowance", "Festival allowance"],
        ["support_staff_allowance", "Allowance for support staff"], ["leave_allowance", "Leave allowance"],
        ["honorarium", "Honorarium, reward, fee"], ["overtime_allowance", "Overtime allowance"],
        ["baishakhi_allowance", "Baishakhi allowance"], ["pf_interest", "Interest accrued on provident fund"],
        ["lamp_grant", "Lamp grant"], ["gratuity", "Gratuity"], ["others", "Others"]
      ].map(function (r) { return { p: "salary.govt." + r[0], l: r[1], t: "num" }; }) },
      { title: "Private sector and others", fields: [
        ["basic_pay", "Basic pay"], ["allowances", "Allowances"], ["advance_salary", "Advance salary"],
        ["gratuity_pension", "Gratuity, annuity, pension"], ["perquisites", "Perquisites"],
        ["in_lieu_of_salary", "In lieu of or in addition to salary"], ["employee_share_scheme", "Employees' share scheme"],
        ["accommodation", "Accommodation benefit"], ["car_benefit", "Car benefit"],
        ["other_benefits", "Other benefits from employer"], ["employer_pf_contribution", "Employer's contribution to recognised PF"],
        ["others", "Others"]
      ].map(function (r) { return { p: "salary.private." + r[0], l: r[1], t: "num" }; }) }
    ] },
    { id: "house", title: "House property", form: "Schedule 2", sum: "r2", list: "house_property",
      add: "Add a property", item: "Property", fields: [
        { p: "description", l: "Location and description", wide: true },
        { p: "type", l: "Use", t: "select", o: [["residential", "Residential (25% repair allowance)"], ["commercial", "Commercial (30%)"]] },
        { p: "annual_value", l: "Rent received or annual value, whichever is higher", t: "num" },
        { p: "advance_rent", l: "Advance rent received", t: "num" },
        { p: "other_benefits", l: "Value of other benefits", t: "num" },
        { p: "adjusted_advance_rent", l: "Adjusted advance rent", t: "num" },
        { p: "vacancy_allowance", l: "Vacancy allowance", t: "num" },
        { p: "municipal_tax", l: "Municipal or local tax", t: "num" },
        { p: "land_revenue", l: "Land revenue", t: "num" },
        { p: "loan_interest", l: "Interest on loan or mortgage", t: "num" },
        { p: "insurance_premium", l: "Insurance premium", t: "num" },
        { p: "other_deductions", l: "Other deductions", t: "num" },
        { p: "ownership_share", l: "Your share", t: "pct", hint: "Leave blank if you own all of it" }
      ] },
    { id: "agri", title: "Agriculture", form: "Schedule 3", sum: "r3", groups: [{ fields: [
      { p: "agriculture.nature", l: "Nature of agriculture", wide: true },
      { p: "agriculture.turnover", l: "Sale, turnover, receipts", t: "num" },
      { p: "agriculture.gross_profit", l: "Gross profit", t: "num" },
      { p: "agriculture.expenses", l: "Expenses, land revenue, interest, insurance", t: "num" }
    ] }] },
    { id: "business", title: "Business or profession", form: "Schedule 4", sum: "r4", groups: [
      { fields: [
        { p: "business.name", l: "Name of business or profession" },
        { p: "business.nature", l: "Nature of business" },
        { p: "business.address", l: "Address", wide: true },
        { p: "business.turnover", l: "Sale, turnover, receipts", t: "num" },
        { p: "business.gross_profit", l: "Gross profit", t: "num" },
        { p: "business.expenses", l: "General, administrative, selling expenses", t: "num" },
        { p: "business.bad_debt", l: "Bad debt", t: "num" }
      ] },
      { title: "Balance sheet at 30 June", fields: [
        { p: "business.balance_sheet.cash_bank", l: "Cash and bank", t: "num" },
        { p: "business.balance_sheet.inventory", l: "Inventory", t: "num" },
        { p: "business.balance_sheet.fixed_assets", l: "Fixed assets", t: "num" },
        { p: "business.balance_sheet.other_assets", l: "Other assets", t: "num" },
        { p: "business.balance_sheet.opening_capital", l: "Opening capital", t: "num" },
        { p: "business.balance_sheet.drawings", l: "Drawings during the year", t: "num" },
        { p: "business.balance_sheet.liabilities", l: "Liabilities", t: "num" }
      ] }
    ] },
    { id: "other", title: "Other income", form: "Return lines 5-10", groups: [{ fields: [
      { p: "other_income.capital_gains", l: "Capital gains", t: "num" },
      { p: "other_income.financial_assets", l: "Bank interest, dividend, securities", t: "num" },
      { p: "other_income.sanchayapatra_interest", l: "Savings certificate (sanchayapatra) interest", t: "num",
        hint: "Taxed finally at source; also enter its AIT under tax paid" },
      { p: "other_income.other_sources", l: "Other sources (royalty, honorarium, fees)", t: "num" },
      { p: "other_income.firm_share", l: "Share of income from firm or AOP", t: "num" },
      { p: "other_income.minor_spouse", l: "Income of minor or spouse", t: "num" },
      { p: "other_income.foreign", l: "Foreign income", t: "num" }
    ] }] },
    { id: "exempt", title: "Tax-free income", form: "Return line 26", sum: "r26",
      note: "The salary exemption is added automatically.", groups: [{ fields: [
        ["salary_other", "Other salary exemption"], ["govt_pf", "Government provident fund (up to Tk 2.5 crore)"],
        ["taxed_distribution", "Income already taxed, distributed to beneficiaries"],
        ["pf_1925_income", "Income of a provident fund (Act 1925)"], ["voluntary_retirement", "Voluntary retirement scheme"],
        ["pensioners_savings_certificate", "Pensioners' savings certificate (up to Tk 5 lakh)"],
        ["firm_capital_share", "Share of firm income taxed in the firm"], ["huf_share", "Share from a Hindu undivided family"],
        ["foreign_remittance", "Foreign remittance"], ["wage_earners_fund", "Wage earners' development fund"],
        ["hill_tracts", "Income from Bandarban, Khagrachari, Rangamati"], ["agricultural", "Agricultural income (exempt part)"],
        ["software_it", "Software and IT business"], ["handicrafts_export", "Export of handicrafts"],
        ["sme", "Small and medium industries"], ["zero_coupon", "Zero coupon bonds"],
        ["govt_pension", "Government pension"], ["welfare_allowance", "Welfare allowance, Muktijoddha Kallyan Trust"],
        ["govt_award", "Award money from the Government"], ["briddhashram", "Management of a briddhashram"],
        ["seagoing_ship", "Bangladeshi-flagged ship bringing foreign currency"], ["other", "Other 6th Schedule exemption"]
      ].map(function (r) { return { p: "exempt_income." + r[0], l: r[1], t: "num" }; }) }] },
    { id: "invest", title: "Investments for rebate", form: "Schedule 5", sum: "r13", sumLabel: "rebate", groups: [{ fields: [
      ["life_insurance", "Life insurance premium"], ["dps", "Deposit pension scheme (DPS)"],
      ["govt_securities", "Government securities, savings certificates, unit certificates"],
      ["listed_securities", "Listed shares and securities"], ["pf_1925", "Provident fund (Act 1925)"],
      ["rpf", "Recognised provident fund (own + employer)"], ["pension_fund", "Approved pension fund"],
      ["benevolent_group_insurance", "Benevolent fund and group insurance"], ["zakat", "Zakat fund"], ["others", "Others"]
    ].map(function (r) { return { p: "investments." + r[0], l: r[1], t: "num" }; }) }] },
    { id: "paid", title: "Tax paid and other charges", form: "Return lines 17-25", sum: "r24", sumLabel: "paid", groups: [
      { title: "Tax already paid", fields: [
        { p: "payments.tds_salary", l: "Tax deducted from salary", t: "num" },
        { p: "payments.ait_sanchayapatra", l: "AIT on savings certificates", t: "num" },
        { p: "payments.ait_bank_interest", l: "AIT on bank interest", t: "num" },
        { p: "payments.ait_wppf", l: "AIT on WPPF", t: "num" },
        { p: "payments.ait_car", l: "AIT with car tax token", t: "num" },
        { p: "payments.advance_tax", l: "Advance tax by treasury challan", t: "num" },
        { p: "payments.refund_adjustment", l: "Refund adjusted from earlier years", t: "num" },
        { p: "payments.refund_assessment_years", l: "Assessment years of that refund" },
        { p: "payments.paid_with_return", l: "Paid with the return (A-challan)", t: "optnum",
          hint: "Leave blank to assume the balance is paid" },
        { p: "payments.challan_number", l: "A-challan number" }
      ] },
      { title: "Other charges", fields: [
        { p: "tax.surcharge_trigger", l: "Owns more than one car, or a house over 8,000 sft in a city corporation", t: "check", wide: true },
        { p: "tax.environmental_surcharge", l: "Environmental surcharge (cars)", t: "num" },
        { p: "tax.delay_interest", l: "Delay interest or penalty", t: "num" },
        { p: "tax.min_tax_163_2kha", l: "Minimum tax u/s 163(2)(kha)", t: "num" },
        { p: "tax.min_tax_163_5ka", l: "Minimum tax u/s 163(5)(ka)", t: "num" }
      ] }
    ] },
    { id: "life", title: "Living expenses", form: "IT-10BB", sum: "lb.total", groups: [{ fields: [
      { p: "lifestyle.food_clothing", l: "Food, clothing and essentials", t: "num" },
      { p: "lifestyle.housing", l: "Housing", t: "num" },
      { p: "lifestyle.comments.housing", l: "Housing note", hint: "For example: Family House" },
      { p: "lifestyle.transport", l: "Personal transport", t: "num" },
      { p: "lifestyle.utility", l: "Electricity, gas, water, phone, internet", t: "num" },
      { p: "lifestyle.education", l: "Education", t: "num" },
      { p: "lifestyle.travel", l: "Travel and holidays", t: "num" },
      { p: "lifestyle.festival", l: "Festivals and special occasions", t: "num" },
      { p: "lifestyle.loan_interest", l: "Interest on personal loans", t: "num" },
      { p: "lifestyle.tax_paid", l: "Tax paid (row 8)", t: "optnum", hint: "Leave blank to use this return's tax paid" }
    ] }] },
    { id: "wealth", title: "Assets and liabilities", form: "IT-10B", sum: "w.5", sumLabel: "net wealth", groups: [
      { fields: [
        { p: "wealth.previous_net_wealth", l: "Net wealth on last year's IT-10B", t: "optnum", hint: "Leave blank on a first return" },
        { p: "wealth.balancing_item", l: "Balance the statement with", t: "select", o: [
          ["", "Automatic (gift on a first return, otherwise cash)"], ["cash", "Cash and bank"],
          ["gift", "Receipt of gift and others"], ["none", "Nothing (I enter every figure)"]] },
        { p: "wealth.gift_and_other_receipts", l: "Receipt of gift and others", t: "num", hint: "Used unless it is the balancing figure" },
        { p: "wealth.other_outflows", l: "Gifts given, losses, expenses not in IT-10BB", t: "num" }
      ] },
      { title: "Liabilities", fields: [
        { p: "wealth.liabilities.institutional", l: "Bank and institutional loans", t: "num" },
        { p: "wealth.liabilities.non_institutional", l: "Non-institutional loans", t: "num" },
        { p: "wealth.liabilities.other", l: "Other liabilities", t: "num" }
      ] },
      { title: "Property", lists: [
        { list: "wealth.assets.non_agricultural_property", item: "Non-agricultural property", add: "Add land, building or flat",
          fields: [{ p: "description", l: "Description, location and size", wide: true }, { p: "value", l: "Cost value", t: "num" }] },
        { list: "wealth.assets.agricultural_property", item: "Agricultural land", add: "Add agricultural land",
          fields: [{ p: "description", l: "Description, location and size", wide: true }, { p: "value", l: "Cost value", t: "num" }] }
      ] },
      { title: "Financial assets", fields: [
        { p: "wealth.assets.debenture_bond", l: "Debentures, bonds, shares, unit certificates", t: "num" },
        { p: "wealth.assets.sanchayapatra_dps", l: "Savings certificates and DPS", t: "num" },
        { p: "wealth.assets.life_insurance", l: "Life insurance (premiums paid)", t: "num" },
        { p: "wealth.assets.loan_given", l: "Loans given", t: "num" },
        { p: "wealth.assets.fdr", l: "Fixed deposits", t: "num" },
        { p: "wealth.assets.provident_fund", l: "Provident fund and other funds", t: "num" },
        { p: "wealth.assets.other_investment", l: "Other investments", t: "num" }
      ] },
      { title: "Other assets", fields: [
        { p: "wealth.assets.director_shareholdings", l: "Director's shareholdings in limited companies", t: "num" },
        { p: "wealth.assets.motor_car", l: "Motor car (cost)", t: "num" },
        { p: "wealth.assets.motor_car_details", l: "Car type and registration number" },
        { p: "wealth.assets.ornaments", l: "Ornaments (value)", t: "num" },
        { p: "wealth.assets.ornaments_quantity", l: "Ornaments quantity", hint: "For example: 25 Bhori" },
        { p: "wealth.assets.ornaments_note", l: "Ornaments note", hint: "For example: (Wedding Gifts)" },
        { p: "wealth.assets.furniture_electronics", l: "Furniture and electronics", t: "num" },
        { p: "wealth.assets.furniture_note", l: "Furniture note" },
        { p: "wealth.assets.other_assets", l: "Other assets", t: "num" },
        { p: "wealth.assets.cash_bank", l: "Cash, bank and funds outside business", t: "num",
          hint: "Worked out for you when cash is the balancing figure" }
      ] }
    ] },
    { id: "sign", title: "Signing and documents", groups: [{ fields: [
      { p: "form.place", l: "Place" },
      { p: "form.date", l: "Date", t: "date" },
      { p: "form.documents", l: "Documents attached (one per line, up to 7)", t: "lines", wide: true }
    ] }] }
  ];

  // ---------------------------------------------------------------- helpers
  function h(tag, attrs, kids) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) { if (c) el.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return el;
  }
  function getP(o, path) {
    var parts = path.split(".");
    for (var i = 0; i < parts.length; i++) { if (o === null || o === undefined) return undefined; o = o[parts[i]]; }
    return o;
  }
  function setP(o, path, v) {
    var parts = path.split(".");
    for (var i = 0; i < parts.length - 1; i++) {
      if (!o[parts[i]] || typeof o[parts[i]] !== "object") o[parts[i]] = {};
      o = o[parts[i]];
    }
    if (v === undefined) delete o[parts[parts.length - 1]]; else o[parts[parts.length - 1]] = v;
  }
  function money(v) {
    if (v === null || v === undefined || isNaN(v)) return "-";
    var r = BDERCalc.rnd(v);
    if (r === 0) return "-";
    var s = Math.abs(r).toLocaleString("en-US");
    return r < 0 ? "(" + s + ")" : s;
  }
  function slug(s) { return String(s || "return").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "") || "return"; }
  function today() {
    var d = new Date();
    return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  }
  var uid = 0;

  function freshData(profile) {
    return {
      rules_profile: profile, assessment_year: CFG.assessmentYear || "2026-2027",
      taxpayer: { resident: true, gender: "male", relation: "father" },
      form: { special_benefit_boxes: "auto", documents: DEFAULT_DOCS.slice(), date: today() },
      house_property: [], wealth: { assets: { non_agricultural_property: [], agricultural_property: [] } }
    };
  }

  // ------------------------------------------------------------------ app
  function App(root) {
    this.root = root;
    this.base = root.getAttribute("data-base") || CFG.assetsUrl || "assets/";
    this.defaultProfile = root.getAttribute("data-profile") || CFG.defaultProfile || PROFILES[0];
    this.data = null;
    this.assets = null;
    this.result = null;
    this.timer = null;
    this.pdfUrl = null;
  }

  App.prototype.start = function () {
    var self = this;
    this.root.classList.add("bder");
    this.root.innerHTML = "";
    this.root.appendChild(h("p", { class: "bder-loading", text: "Loading the return form..." }));
    BDERRender.loadAssets(this.base, PROFILES).then(function (assets) {
      self.assets = assets;
      self.data = self.restore() || freshData(self.defaultProfile);
      self.build();
      self.recalc();
    }).catch(function (e) {
      self.root.innerHTML = "";
      self.root.appendChild(h("p", { class: "bder-error", text: "The form could not load its files: " + e.message +
        ". Check that the plugin's assets folder is reachable." }));
    });
  };

  App.prototype.restore = function () {
    try {
      var raw = window.localStorage.getItem(STORE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  };
  App.prototype.persist = function () {
    try { window.localStorage.setItem(STORE_KEY, JSON.stringify(this.data)); } catch (e) { /* storage unavailable */ }
  };

  App.prototype.build = function () {
    var self = this, d = this.data;
    var profileSel = h("select", { id: "bder-profile", onchange: function () { d.rules_profile = this.value; self.changed(); } },
      PROFILES.map(function (id) {
        var t = PROFILE_LABELS[id] || (self.assets.profiles[id] && self.assets.profiles[id].title) || id;
        return h("option", { value: id, text: t });
      }));
    profileSel.value = d.rules_profile || this.defaultProfile;
    var aySel = h("input", { id: "bder-ay", value: d.assessment_year || "2026-2027", size: "9",
      oninput: function () { d.assessment_year = this.value; self.changed(); } });

    var head = h("header", { class: "bder-head" }, [
      h("div", { class: "bder-title" }, [
        h("h2", { text: "Income tax return" }),
        h("p", { text: "Fill in the taxpayer's figures. The tax is worked out as you type, and the 12-page return " +
          "(IT-11GA 2023, schedules, IT-10BB, IT-10B, tax computation) prints exactly like the template." })
      ]),
      h("div", { class: "bder-settings" }, [
        h("label", { for: "bder-ay" }, ["Assessment year", aySel]),
        h("label", { for: "bder-profile" }, ["Tax rules", profileSel])
      ]),
      h("div", { class: "bder-tools" }, [
        h("button", { type: "button", class: "bder-btn bder-quiet", onclick: function () { self.loadExample(); }, text: "Load example" }),
        h("button", { type: "button", class: "bder-btn bder-quiet", onclick: function () { self.saveJson(); }, text: "Save data" }),
        h("label", { class: "bder-btn bder-quiet bder-file" }, ["Open saved data",
          h("input", { type: "file", accept: ".json,application/json", onchange: function () { self.openJson(this); } })]),
        h("button", { type: "button", class: "bder-btn bder-quiet", onclick: function () { self.clear(); }, text: "Clear form" })
      ])
    ]);

    var form = h("div", { class: "bder-form" });
    SECTIONS.forEach(function (sec, i) { form.appendChild(self.section(sec, i)); });

    this.panel = h("aside", { class: "bder-panel", id: "bder-panel", "aria-label": "Tax computation" });
    this.dialog = h("dialog", { class: "bder-dialog" });
    // Shown only when the form is one column wide: the amount due stays in view while typing.
    this.mini = h("div", { class: "bder-mini" });

    this.root.innerHTML = "";
    this.root.appendChild(head);
    this.root.appendChild(h("div", { class: "bder-body" }, [form, this.panel]));
    this.root.appendChild(this.mini);
    this.root.appendChild(this.dialog);
  };

  App.prototype.section = function (sec, index) {
    var self = this;
    var total = h("span", { class: "bder-sum", "data-sum": sec.sum || "" });
    var summary = h("summary", null, [
      h("span", { class: "bder-sec-title" }, [sec.title, sec.form ? h("small", { text: sec.form }) : null]),
      total
    ]);
    var det = h("details", { class: "bder-sec", id: "bder-sec-" + sec.id }, [summary]);
    if (index === 0) det.open = true;
    var body = h("div", { class: "bder-sec-body" });
    if (sec.note) body.appendChild(h("p", { class: "bder-note", text: sec.note }));
    if (sec.list) body.appendChild(this.listEditor({ list: sec.list, item: sec.item, add: sec.add, fields: sec.fields }));
    (sec.groups || []).forEach(function (g) {
      var box = h("fieldset", { class: "bder-group" }, g.title ? [h("legend", { text: g.title })] : []);
      if (g.fields) box.appendChild(self.grid(g.fields, self.data, ""));
      (g.lists || []).forEach(function (l) { box.appendChild(self.listEditor(l)); });
      body.appendChild(box);
    });
    det.appendChild(body);
    return det;
  };

  App.prototype.grid = function (fields, target, prefix) {
    var self = this, grid = h("div", { class: "bder-grid" });
    fields.forEach(function (f) { grid.appendChild(self.field(f, target, prefix)); });
    return grid;
  };

  App.prototype.field = function (f, target, prefix) {
    var self = this, t = f.t || "text", id = "bder-f" + (++uid), cur = getP(target, f.p), input;
    function set(v) { setP(target, f.p, v); self.changed(); }
    var wrapCls = "bder-field" + (f.wide ? " bder-wide" : "") + (t === "check" || t === "boxes" ? " bder-checkfield" : "");

    if (t === "check" || t === "boxes") {
      input = h("input", { type: "checkbox", id: id });
      input.checked = t === "boxes" ? cur === undefined || cur === "auto" : !!cur;
      input.addEventListener("change", function () { set(t === "boxes" ? (this.checked ? "auto" : []) : this.checked); });
      return h("div", { class: wrapCls }, [input, h("label", { for: id }, [f.l, f.hint ? h("small", { text: f.hint }) : null])]);
    }
    if (t === "multi") {
      var chosen = Array.isArray(cur) ? cur.slice() : [];
      var opts = f.o.map(function (o) {
        var oid = id + "-" + o[0];
        var cb = h("input", { type: "checkbox", id: oid, value: o[0] });
        cb.checked = chosen.indexOf(o[0]) >= 0;
        cb.addEventListener("change", function () {
          var list = (getP(target, f.p) || []).filter(function (x) { return x !== o[0] && x !== "general"; });
          if (this.checked) list.push(o[0]);
          set(list.length ? list : undefined);
        });
        return h("span", { class: "bder-opt" }, [cb, h("label", { for: oid, text: o[1] })]);
      });
      return h("div", { class: wrapCls }, [h("span", { class: "bder-label", text: f.l }), h("div", { class: "bder-opts" }, opts)]);
    }
    if (t === "select") {
      input = h("select", { id: id }, f.o.map(function (o) { return h("option", { value: o[0], text: o[1] }); }));
      input.value = cur === undefined || cur === null ? f.o[0][0] : cur;
      input.addEventListener("change", function () { set(this.value === "" ? undefined : this.value); });
    } else if (t === "area" || t === "lines") {
      input = h("textarea", { id: id, rows: t === "lines" ? "4" : "2" });
      input.value = t === "lines" ? (Array.isArray(cur) ? cur.join("\n") : "") : (cur || "");
      input.addEventListener("input", function () {
        set(t === "lines" ? this.value.split("\n").map(function (s) { return s.trim(); }).filter(Boolean) : this.value);
      });
    } else if (t === "date") {
      input = h("input", { type: "date", id: id });
      input.value = cur || "";
      input.addEventListener("input", function () { set(this.value || undefined); });
    } else if (t === "num" || t === "optnum" || t === "pct") {
      input = h("input", { type: "text", id: id, inputmode: "decimal", class: "bder-num", autocomplete: "off" });
      var shown = cur === undefined || cur === null ? "" : (t === "pct" ? Math.round(cur * 10000) / 100 : cur);
      input.value = shown;
      input.addEventListener("input", function () {
        var raw = this.value.replace(/,/g, "").trim();
        if (raw === "") { set(undefined); this.classList.remove("bder-bad"); return; }
        var n = Number(raw);
        this.classList.toggle("bder-bad", !isFinite(n));
        if (!isFinite(n)) return;
        set(t === "pct" ? (n >= 100 ? undefined : n / 100) : n);
      });
    } else {
      input = h("input", { type: t === "text" && f.im === "email" ? "email" : "text", id: id,
        inputmode: f.im && f.im !== "email" ? f.im : null, autocomplete: "off" });
      input.value = cur === undefined || cur === null ? "" : cur;
      input.addEventListener("input", function () { set(this.value === "" ? undefined : this.value); });
    }
    if (f.req) input.setAttribute("required", "");
    var label = h("label", { for: id }, [f.l, t === "pct" ? " (%)" : null]);
    var hint = f.hint ? h("span", { class: "bder-hint", id: id + "-hint", text: f.hint }) : null;
    if (hint) input.setAttribute("aria-describedby", id + "-hint");
    return h("div", { class: wrapCls }, [label, input, hint]);
  };

  App.prototype.listEditor = function (cfg) {
    var self = this, wrap = h("div", { class: "bder-list" });
    function items() {
      var arr = getP(self.data, cfg.list);
      if (!Array.isArray(arr)) { arr = []; setP(self.data, cfg.list, arr); }
      return arr;
    }
    function draw() {
      wrap.innerHTML = "";
      items().forEach(function (it, i) {
        var box = h("div", { class: "bder-item" }, [
          h("div", { class: "bder-item-head" }, [
            h("strong", { text: cfg.item + " " + (i + 1) }),
            h("button", { type: "button", class: "bder-link", text: "Remove",
              onclick: function () { items().splice(i, 1); draw(); self.changed(); } })
          ]),
          self.grid(cfg.fields, it, "")
        ]);
        wrap.appendChild(box);
      });
      wrap.appendChild(h("button", { type: "button", class: "bder-btn bder-quiet bder-add", text: cfg.add,
        onclick: function () { items().push({}); draw(); self.changed(); } }));
    }
    draw();
    return wrap;
  };

  App.prototype.changed = function () {
    var self = this;
    this.persist();
    clearTimeout(this.timer);
    this.timer = setTimeout(function () { self.recalc(); }, 120);
  };

  /** Compute; missing name/TIN get placeholders so the summary still works. */
  App.prototype.recalc = function () {
    var data = JSON.parse(JSON.stringify(this.data)), missing = [];
    if (!String(getP(data, "taxpayer.name") || "").trim()) { missing.push("name"); setP(data, "taxpayer.name", "-"); }
    if (String(getP(data, "taxpayer.tin") || "").replace(/\D/g, "").length !== 12) {
      missing.push("12-digit TIN"); setP(data, "taxpayer.tin", "000000000000");
    }
    try {
      var res = BDERCalc.compute(data, this.assets.profiles);
      this.result = { V: res.V, warnings: res.warnings, missing: missing, error: null };
    } catch (e) {
      this.result = { V: null, warnings: [], missing: missing, error: e.message };
    }
    this.drawPanel();
  };

  App.prototype.drawPanel = function () {
    var self = this, r = this.result, V = r.V, p = this.panel;
    p.innerHTML = "";
    if (!V) {
      p.appendChild(h("p", { class: "bder-error", text: r.error }));
      return;
    }
    Array.prototype.forEach.call(this.root.querySelectorAll(".bder-sum"), function (el) {
      var k = el.getAttribute("data-sum");
      el.textContent = k && V[k] ? money(V[k]) : "";
    });

    function row(label, value, cls) {
      return h("div", { class: "bder-row" + (cls ? " " + cls : "") }, [h("span", { text: label }), h("span", { class: "bder-amt", text: value })]);
    }
    var slabs = h("div", { class: "bder-slabs" });
    for (var i = 0; i < 6; i++) {
      if (i > 0 && !V["tc.s" + i + ".inc"]) continue;
      slabs.appendChild(h("div", { class: "bder-slab" }, [
        h("span", { text: (i === 0 ? "First " : "Next ") + money(V["tc.s" + i + ".inc"]) }),
        h("span", { text: "at " + V["tc.s" + i + ".rate"] }),
        h("span", { class: "bder-amt", text: money(V["tc.s" + i + ".tax"]) })
      ]));
    }
    var due = V.r23, refund = V.r25 < 0;
    p.appendChild(h("h3", { text: "Tax computation" }));
    p.appendChild(h("div", { class: "bder-ledger", "aria-live": "polite" }, [
      row("A  Total income", money(V.r11)),
      row("Tax-free limit", money(V.threshold), "bder-sub"),
      slabs,
      row("B  Tax on slabs", money(V.r12)),
      row("C  Rebate on investment", money(V.r13)),
      row("E  Minimum tax", money(V.r15)),
      row("F  Tax payable", money(V.r16), "bder-strong"),
      V.r17 ? row("G  Surcharge", money(V.r17)) : null,
      V.r18 ? row("Delay interest and final tax", money(V.r18)) : null,
      row("I  Total payable", money(V.r19), "bder-strong"),
      row("J  Already paid and adjusted", money(V.r20 + V.r21 + V.r22))
    ]));
    p.appendChild(h("div", { class: "bder-due" + (refund ? " bder-refund" : "") }, [
      h("span", { text: refund ? "Refundable" : "Pay with the return" }),
      h("strong", { text: "৳ " + (refund ? money(-V.r25) : money(due)) })
    ]));
    p.appendChild(h("div", { class: "bder-ledger bder-wealth" }, [
      row("Tax-free income", money(V.r26)),
      row("Living expenses (IT-10BB)", money(V["lb.total"])),
      row("Net wealth (IT-10B)", money(V["w.5"])),
      row(V.balancing_mode === "gift" ? "Gift and other receipts (balancing)" :
        V.balancing_mode === "cash" ? "Cash and bank (balancing)" : "Assets entered", money(V.balancing_mode === "gift" ? V["w.1c"] : V["a.k"]))
    ]));

    var canPrint = !r.missing.length;
    this.mini.innerHTML = "";
    this.mini.appendChild(h("a", { href: "#bder-panel", class: "bder-mini-sum" }, [
      h("span", { text: refund ? "Refundable" : "Pay with the return" }),
      h("strong", { text: "\u09f3 " + (refund ? money(-V.r25) : money(due)) })
    ]));
    this.mini.appendChild(h("button", { type: "button", class: "bder-btn bder-primary", disabled: !canPrint,
      onclick: function () { self.pdf("download"); }, text: "Download PDF" }));
    p.appendChild(h("div", { class: "bder-actions" }, [
      h("button", { type: "button", class: "bder-btn bder-primary", disabled: !canPrint,
        onclick: function () { self.pdf("download"); }, text: "Download PDF" }),
      h("button", { type: "button", class: "bder-btn", disabled: !canPrint, onclick: function () { self.pdf("preview"); }, text: "Preview" }),
      h("button", { type: "button", class: "bder-btn", disabled: !canPrint, onclick: function () { self.pdf("print"); }, text: "Print" })
    ]));
    if (!canPrint) p.appendChild(h("p", { class: "bder-note", text: "Enter the taxpayer's " + r.missing.join(" and ") + " to make the PDF." }));

    var warn = r.warnings.filter(function (w) { return w.indexOf("Rules profile") !== 0; });
    var rulesNote = r.warnings.filter(function (w) { return w.indexOf("Rules profile") === 0; });
    if (warn.length) p.appendChild(h("div", { class: "bder-warn", role: "status" }, [h("h4", { text: "Check before filing" }),
      h("ul", null, warn.map(function (w) { return h("li", { text: w }); }))]));
    if (rulesNote.length) p.appendChild(h("p", { class: "bder-rules", text: rulesNote[0].replace(/^Rules profile '[^']*': /, "") }));
  };

  App.prototype.pdf = async function (mode) {
    var self = this, V = this.result && this.result.V;
    if (!V) return;
    var btns = this.panel.querySelectorAll("button");
    Array.prototype.forEach.call(btns, function (b) { b.disabled = true; });
    try {
      var bytes = await BDERRender.render(V, {
        PDFLib: window.PDFLib, fontkit: window.fontkit, template: this.assets.template, fields: this.assets.fields,
        emblem: this.assets.emblem, carlito: this.assets.carlito, carlitoBold: this.assets.carlitoBold, taka: this.assets.taka
      });
      if (this.pdfUrl) URL.revokeObjectURL(this.pdfUrl);
      this.pdfUrl = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
      var fname = "Return-" + slug(V.name) + "-AY-" + V.ay + ".pdf";
      if (mode === "download") {
        var a = h("a", { href: this.pdfUrl, download: fname });
        document.body.appendChild(a); a.click(); a.remove();
      } else this.showPdf(mode, fname);
    } catch (e) {
      window.alert("The PDF could not be made: " + e.message);
    } finally {
      Array.prototype.forEach.call(btns, function (b) { b.disabled = false; });
    }
  };

  App.prototype.showPdf = function (mode, fname) {
    var self = this, dlg = this.dialog;
    dlg.innerHTML = "";
    var frame = h("iframe", { src: this.pdfUrl, title: "Return preview" });
    dlg.appendChild(h("div", { class: "bder-dialog-bar" }, [
      h("strong", { text: fname }),
      h("a", { class: "bder-btn bder-primary", href: this.pdfUrl, download: fname, text: "Download PDF" }),
      h("a", { class: "bder-btn", href: this.pdfUrl, target: "_blank", rel: "noopener", text: "Open in new tab" }),
      h("button", { type: "button", class: "bder-btn", onclick: function () { dlg.close(); }, text: "Close" })
    ]));
    dlg.appendChild(frame);
    if (typeof dlg.showModal === "function") dlg.showModal(); else window.open(this.pdfUrl, "_blank");
    if (mode === "print") frame.addEventListener("load", function () {
      try { frame.contentWindow.focus(); frame.contentWindow.print(); } catch (e) { window.open(self.pdfUrl, "_blank"); }
    });
  };

  App.prototype.saveJson = function () {
    var name = slug(getP(this.data, "taxpayer.name"));
    var blob = new Blob([JSON.stringify(this.data, null, 2)], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = h("a", { href: url, download: "e-return-" + name + "-" + (this.data.assessment_year || "") + ".json" });
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  };

  App.prototype.openJson = function (input) {
    var self = this, file = input.files && input.files[0];
    if (!file) return;
    file.text().then(function (txt) {
      var d = JSON.parse(txt);
      if (!d || typeof d !== "object" || !d.taxpayer) throw new Error("this file is not saved e-return data");
      self.data = d; self.persist(); self.build(); self.recalc();
    }).catch(function (e) { window.alert("Could not open the file: " + e.message); });
    input.value = "";
  };

  App.prototype.loadExample = function () {
    var self = this;
    if (!window.confirm("Replace the form with the example taxpayer?")) return;
    fetch(this.base + "data/examples/sample-reproduction.json").then(function (r) { return r.json(); }).then(function (d) {
      self.data = d; self.persist(); self.build(); self.recalc();
    });
  };

  App.prototype.clear = function () {
    if (!window.confirm("Clear every field? Saved data files are not affected.")) return;
    try { window.localStorage.removeItem(STORE_KEY); } catch (e) { /* ignore */ }
    this.data = freshData(this.defaultProfile);
    this.build();
    this.recalc();
  };

  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll(".bder-app"), function (el) {
      if (el.getAttribute("data-started")) return;
      el.setAttribute("data-started", "1");
      new App(el).start();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
