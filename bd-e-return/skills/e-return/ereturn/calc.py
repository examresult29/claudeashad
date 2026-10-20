"""Calculation engine for the Bangladesh individual return of income.

Takes the input dictionary described in docs/INPUT.md and returns a flat dict
holding every figure printed on the 12-page return (IT-11 Chha acknowledgement,
IT-11GA 2023 pages 1-3, Schedules 1-5, IT-10BB, IT-10B, tax computation sheet
and tax-free income sheet), plus a list of warnings.

Money is whole taka. Tax figures are rounded half-up to the taka at the points
the Excel template rounds its displayed values, so every page agrees with the
others.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

RULES_DIR = Path(__file__).parent / "rules"
DEFAULT_PROFILE = "ay2026-27"

# Schedule 1(a): employees paid under the Government pay scale, in form order.
GOVT_ROWS = [
    "basic_pay", "arrear_pay", "special_allowance", "house_rent_allowance",
    "medical_allowance", "conveyance_allowance", "festival_allowance",
    "support_staff_allowance", "leave_allowance", "honorarium",
    "overtime_allowance", "baishakhi_allowance", "pf_interest", "lamp_grant",
    "gratuity", "others",
]
# Schedule 1(b): all other employees, in form order.
PRIVATE_ROWS = [
    "basic_pay", "allowances", "advance_salary", "gratuity_pension",
    "perquisites", "in_lieu_of_salary", "employee_share_scheme",
    "accommodation", "car_benefit", "other_benefits",
    "employer_pf_contribution", "others",
]
# Schedule 5 rows 1-10.
INVEST_ROWS = [
    "life_insurance", "dps", "govt_securities", "listed_securities", "pf_1925",
    "rpf", "pension_fund", "benevolent_group_insurance", "zakat", "others",
]
# Tax-free income sheet rows 02-22 (row 01 is the salary exemption).
TAXFREE_ROWS = [
    "govt_pf", "taxed_distribution", "pf_1925_income", "voluntary_retirement",
    "pensioners_savings_certificate", "firm_capital_share", "huf_share",
    "foreign_remittance", "wage_earners_fund", "hill_tracts", "agricultural",
    "software_it", "handicrafts_export", "sme", "zero_coupon", "govt_pension",
    "welfare_allowance", "govt_award", "briddhashram", "seagoing_ship", "other",
]
# IT-10BB rows 1-9.
LIFESTYLE_ROWS = [
    "food_clothing", "housing", "transport", "utility", "education", "travel",
    "festival", "tax_paid", "loan_interest",
]
CATEGORIES = [
    "general", "female", "senior", "disabled", "third_gender",
    "war_wounded_freedom_fighter", "july_joddha",
]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class InputError(ValueError):
    """Raised when the input cannot produce a valid return."""


def rnd(x) -> int:
    """Excel ROUND(x, 0): half away from zero."""
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def num(v) -> float:
    """Read an amount: accepts numbers, '1,23,456', '' and None."""
    if v is None or v == "":
        return 0
    if isinstance(v, (int, float)):
        return v
    s = str(v).replace(",", "").replace("Tk", "").replace("৳", "").strip()
    return float(s) if s else 0


def opt(v):
    """Like num() but keeps 'not given' (None/'') as None."""
    return None if v is None or v == "" else num(v)


def load_rules(profile: str) -> dict:
    path = RULES_DIR / f"{profile}.json"
    if not path.exists():
        known = sorted(p.stem for p in RULES_DIR.glob("*.json"))
        raise InputError(f"Unknown rules_profile '{profile}'. Available: {', '.join(known)}")
    rules = json.loads(path.read_text(encoding="utf-8"))
    if len(rules["slabs"]) != 5 or rules["slabs"][-1]["width"] is not None:
        raise InputError("A rules profile needs exactly 5 slabs after the tax-free band, the last open-ended "
                         "(the tax computation sheet has 6 slab rows).")
    return rules


def parse_date(v) -> date | None:
    if not v:
        return None
    if isinstance(v, date):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise InputError(f"Cannot read date '{v}'. Use YYYY-MM-DD or DD/MM/YYYY.")


def norm_ay(v) -> tuple[str, int]:
    """'2026-27' / '2026-2027' -> ('2026-2027', 2026)."""
    m = re.fullmatch(r"\s*(\d{4})\s*[-/]\s*(\d{2}|\d{4})\s*", str(v or ""))
    if not m:
        raise InputError(f"assessment_year '{v}' should look like 2026-2027.")
    start = int(m.group(1))
    return f"{start}-{start + 1}", start


def pct(rate: float) -> str:
    p = rate * 100
    return f"{p:.0f}%" if abs(p - round(p)) < 1e-9 else f"{p:g}%"


def digits(s: str) -> str:
    return re.sub(r"\D", "", str(s or ""))


def compute(inp: dict) -> tuple[dict, list[str]]:
    W: list[str] = []
    V: dict = {}
    tp = inp.get("taxpayer", {})
    form = inp.get("form", {})

    profile = inp.get("rules_profile") or DEFAULT_PROFILE
    R = load_rules(profile)
    V["rules_profile"] = profile
    if R.get("warning"):
        W.append(f"Rules profile '{profile}': {R['warning']}")

    # ---------------------------------------------------------------- identity
    ay, ay_start = norm_ay(inp.get("assessment_year", "2026-2027"))
    iy_end = date(ay_start, 6, 30)
    V["ay"] = ay
    V["iy_end_mdy"] = f"{iy_end.month}/{iy_end.day}/{iy_end.year}"
    V["iy_end_dmy"] = f"{iy_end.day}-{MONTHS[iy_end.month - 1]}-{iy_end.year % 100:02d}"

    name = (tp.get("name") or "").strip()
    if not name:
        raise InputError("taxpayer.name is required.")
    V["name"] = name
    V["name_line"] = f"Name: {name}"
    tin = digits(tp.get("tin"))
    if len(tin) != 12:
        raise InputError(f"taxpayer.tin must have 12 digits (got '{tp.get('tin')}').")
    V["tin"] = tin
    V["nid"] = str(tp.get("nid") or tp.get("passport") or "")
    V["circle"] = str(tp.get("circle") or "")
    V["zone"] = str(tp.get("tax_zone") or "")
    resident = tp.get("resident", True)
    V["resident"] = bool(resident)
    V["nonresident"] = not resident
    dob = parse_date(tp.get("dob"))
    V["dob_digits"] = dob.strftime("%d%m%Y") if dob else ""
    for k in ("spouse_name", "spouse_tin", "address", "telephone", "mobile", "email",
              "employer", "organization", "bin", "partners", "father_or_husband"):
        V[k] = str(tp.get(k) or "")
    V["relation"] = (tp.get("relation") or "father").lower()
    V["place"] = str(form.get("place") or "")
    sign_date = parse_date(form.get("date"))
    V["date"] = sign_date.strftime("%d/%m/%Y") if sign_date else ""
    docs = form.get("documents")
    if docs is None:
        docs = ["Tax Calculation", "Tax Free Income/ Exempted", "Related Supporting Documents"]
    for i in range(7):
        V[f"doc{i + 1}"] = docs[i] if i < len(docs) else ""
    if len(docs) > 7:
        W.append("Only 7 documents fit in the list on page 3; the rest were left out.")

    # Special-benefit category -> tax-free threshold.
    cats = tp.get("category") or ["general"]
    cats = [cats] if isinstance(cats, str) else list(cats)
    gender = (tp.get("gender") or "").lower()
    if gender == "female" and "female" not in cats:
        cats.append("female")
    if gender in ("third_gender", "third gender") and "third_gender" not in cats:
        cats.append("third_gender")
    age = None
    if dob:
        age = iy_end.year - dob.year - ((iy_end.month, iy_end.day) < (dob.month, dob.day))
        if age >= 65 and "senior" not in cats:
            cats.append("senior")
    for c in cats:
        if c not in CATEGORIES:
            raise InputError(f"Unknown category '{c}'. Use one of: {', '.join(CATEGORIES)}")
    parent = bool(tp.get("parent_of_disabled"))
    threshold = max(R["thresholds"][c] for c in cats)
    if parent:
        threshold += R["thresholds"]["parent_of_disabled_addition"]
    V["threshold"] = threshold

    boxes = form.get("special_benefit_boxes", "auto")
    if boxes == "auto":
        boxes = [c for c in cats if c != "general"] + (["parent_of_disabled"] if parent else [])
    for box, key in (("war_wounded_freedom_fighter", "box.ff"), ("female", "box.female"),
                     ("third_gender", "box.third"), ("disabled", "box.disabled"),
                     ("senior", "box.65"), ("parent_of_disabled", "box.parent")):
        V[key] = box in boxes
    if "july_joddha" in boxes:
        V["box.ff"] = True  # the 2023 form has no separate box; the freedom-fighter box is the closest

    # ------------------------------------------------------ Schedule 1 salary
    sal = inp.get("salary", {})
    gov = sal.get("govt", {})
    taxable_items = set(sal.get("govt_taxable_items") or R["govt_salary_taxable_items"])
    inc_t = exm_t = tax_t = 0
    for k in GOVT_ROWS:
        a = num(gov.get(k))
        V[f"s1a.{k}.inc"] = a
        if k in taxable_items:
            V[f"s1a.{k}.exm"], V[f"s1a.{k}.tax"] = None, a
            tax_t += a
        else:
            V[f"s1a.{k}.exm"], V[f"s1a.{k}.tax"] = a, None
            exm_t += a
        inc_t += a
    V["s1a.inc"], V["s1a.exm"], V["s1a.tax"] = inc_t, exm_t, tax_t

    pri = sal.get("private", {})
    p_total = 0
    for k in PRIVATE_ROWS:
        a = num(pri.get(k))
        V[f"s1b.{k}"] = a
        p_total += a
    ex = R["private_salary_exemption"]
    p_exempt = rnd(min(p_total * ex["fraction"], ex["cap"])) if p_total > 0 else 0
    if sal.get("private_exemption") is not None:
        p_exempt = num(sal["private_exemption"])
    V["s1b.sub"] = V["s1b.total"] = p_total
    V["s1b.exempt"] = p_exempt
    V["s1b.net"] = p_total - p_exempt

    # --------------------------------------------- Schedule 2 house property
    props = inp.get("house_property") or []
    if isinstance(props, dict):
        props = [props]
    rows = {k: 0 for k in ("r1", "r2", "r3", "r4", "r5", "r6", "da", "db", "dc", "dd", "de", "df", "r8", "r9")}
    share_income = 0
    partial = False
    rates = set()
    descs = []
    for p in props:
        r1, r2, r3 = num(p.get("annual_value")), num(p.get("advance_rent")), num(p.get("other_benefits"))
        r4, r5 = num(p.get("adjusted_advance_rent")), num(p.get("vacancy_allowance"))
        r6 = r1 + r2 + r3 - r4 - r5
        kind = (p.get("type") or "residential").lower()
        rate = p.get("repair_rate")
        rate = num(rate) if rate is not None else R["house_repair_rate"].get(kind)
        if rate is None:
            raise InputError(f"house_property.type '{kind}' must be residential or commercial.")
        rates.add(rate)
        da = rnd(r6 * rate)
        db, dc, dd = num(p.get("municipal_tax")), num(p.get("land_revenue")), num(p.get("loan_interest"))
        de, df = num(p.get("insurance_premium")), num(p.get("other_deductions"))
        r8 = da + db + dc + dd + de + df
        r9 = r6 - r8
        share = p.get("ownership_share")
        if share is not None and float(share) < 1:
            partial = True
            share_income += rnd(r9 * float(share))
        else:
            share_income += r9
        for k, a in zip(("r1", "r2", "r3", "r4", "r5", "r6", "da", "db", "dc", "dd", "de", "df", "r8", "r9"),
                        (r1, r2, r3, r4, r5, r6, da, db, dc, dd, de, df, r8, r9)):
            rows[k] += a
        if p.get("description"):
            descs.append(str(p["description"]))
    for k, a in rows.items():
        V[f"s2.{k}"] = a
    V["s2.r7"] = rows["r8"]
    V["s2.r10"] = share_income if partial else None
    V["s2.rate"] = pct(rates.pop()) if len(rates) == 1 else ("Mixed" if rates else pct(R["house_repair_rate"]["residential"]))
    V["s2.desc"] = "; ".join(descs)
    house_income = share_income if props else 0

    # ------------------------------------------------ Schedule 3 agriculture
    ag = inp.get("agriculture", {})
    V["s3.nature"] = str(ag.get("nature") or "")
    V["s3.r1"], V["s3.r2"], V["s3.r3"] = num(ag.get("turnover")), num(ag.get("gross_profit")), num(ag.get("expenses"))
    V["s3.r4"] = V["s3.r2"] - V["s3.r3"]

    # --------------------------------------------------- Schedule 4 business
    bz = inp.get("business", {})
    bs = bz.get("balance_sheet", {})
    V["s4.name"], V["s4.nature"], V["s4.address"] = (str(bz.get(k) or "") for k in ("name", "nature", "address"))
    V["s4.r1"], V["s4.r2"] = num(bz.get("turnover")), num(bz.get("gross_profit"))
    V["s4.r3"], V["s4.r4"] = num(bz.get("expenses")), num(bz.get("bad_debt"))
    V["s4.r5"] = V["s4.r2"] - V["s4.r3"] - V["s4.r4"]
    V["s4.r6"], V["s4.r7"] = num(bs.get("cash_bank")), num(bs.get("inventory"))
    V["s4.r8"], V["s4.r9"] = num(bs.get("fixed_assets")), num(bs.get("other_assets"))
    V["s4.r10"] = V["s4.r6"] + V["s4.r7"] + V["s4.r8"] + V["s4.r9"]
    V["s4.r11"], V["s4.r12"], V["s4.r13"] = num(bs.get("opening_capital")), V["s4.r5"], num(bs.get("drawings"))
    V["s4.r14"] = V["s4.r11"] + V["s4.r12"] - V["s4.r13"]
    V["s4.r15"] = num(bs.get("liabilities"))
    V["s4.r16"] = V["s4.r14"] + V["s4.r15"]
    if bs and abs(V["s4.r16"] - V["s4.r10"]) >= 1:
        W.append(f"Schedule 4 balance sheet does not balance: total assets {V['s4.r10']:,.0f} vs "
                 f"capital + liabilities {V['s4.r16']:,.0f}.")

    # -------------------------------------------------- total income (1-11)
    oi = inp.get("other_income", {})
    sanchaya = num(oi.get("sanchayapatra_interest"))
    V["r1"] = V["s1a.tax"] + V["s1b.net"]
    V["r2"] = house_income
    V["r3"] = V["s3.r4"]
    V["r4"] = V["s4.r5"]
    V["r5"] = num(oi.get("capital_gains"))
    V["r6"] = num(oi.get("financial_assets")) + sanchaya
    V["r7"] = num(oi.get("other_sources"))
    V["r8"] = num(oi.get("firm_share"))
    V["r9"] = num(oi.get("minor_spouse"))
    V["r10"] = num(oi.get("foreign"))
    V["r11"] = sum(V[f"r{i}"] for i in range(1, 11))

    # ------------------------------------------------- tax-free income sheet
    tf = inp.get("exempt_income", {})
    V["tf.r01"] = V["s1a.exm"] + V["s1b.exempt"] + num(tf.get("salary_other"))
    for i, k in enumerate(TAXFREE_ROWS, start=2):
        V[f"tf.r{i:02d}"] = num(tf.get(k))
    V["tf.total"] = sum(V[f"tf.r{i:02d}"] for i in range(1, 23))
    V["r26"] = V["tf.total"]

    # ------------------------------------------------ A. income for the slabs
    V["tc.A"] = V["r11"]
    V["tc.sp"] = sanchaya
    A = V["tc.An"] = V["r11"] - sanchaya

    # --------------------------------------------------------- B. slab tax
    bands = [(threshold, 0.0)] + [(s["width"], s["rate"]) for s in R["slabs"]]
    rest = max(A, 0)
    gross = 0.0
    for i, (width, rate) in enumerate(bands):
        part = rest if width is None else min(rest, width)
        rest -= part
        V[f"tc.s{i}.inc"] = part
        V[f"tc.s{i}.rate"] = pct(rate)
        V[f"tc.s{i}.tax"] = part * rate
        gross += part * rate
    V["tc.sinc"] = max(A, 0)
    B = V["tc.B"] = rnd(gross)

    # --------------------------------------------------------- C. rebate
    inv = inp.get("investments", {})
    total_inv = 0
    for i, k in enumerate(INVEST_ROWS, start=1):
        a = num(inv.get(k))
        V[f"s5.r{i}"] = a
        total_inv += a
    V["s5.r11"] = total_inv
    rb = R["rebate"]
    V["tc.ci"] = max(A, 0) * rb["income_rate"]
    V["tc.cii"] = total_inv * rb["investment_rate"]
    V["tc.ciii"] = rb["cap"]
    C = V["tc.C"] = rnd(min(V["tc.ci"], V["tc.cii"], V["tc.ciii"]))
    if inp.get("tax", {}).get("rebate_allowed") is False:
        C = V["tc.C"] = 0
    V["s5.r12"] = C
    C_used = min(C, B)
    D = V["tc.D"] = B - C_used

    # ---------------------------------------------------- E. minimum tax
    tx = inp.get("tax", {})
    mt = R["minimum_tax"]
    if A <= threshold:
        e1 = 0
    elif mt["mode"] == "flat":
        e1 = mt["first_return_amount"] if tp.get("first_return") else mt["amount"]
    else:
        loc = tp.get("location") or "other"
        e1 = mt["locations"][loc]
    if tx.get("minimum_tax") is not None:
        e1 = num(tx["minimum_tax"])
    V["tc.ei"], V["tc.eii"], V["tc.eiii"] = e1, num(tx.get("min_tax_163_2kha")), num(tx.get("min_tax_163_5ka"))
    E = V["tc.E"] = max(V["tc.ei"], V["tc.eii"], V["tc.eiii"])
    F = V["tc.F"] = max(D, E)
    if E > D and F > 0:
        W.append(f"Minimum tax applies: computed tax after rebate is {D:,} but the minimum is {E:,}.")

    # --------------------------------------------- payments (J) and wealth
    pay = inp.get("payments", {})
    for i, k in enumerate(("tds_salary", "ait_sanchayapatra", "ait_wppf", "ait_car", "ait_bank_interest",
                           "refund_adjustment", "advance_tax"), start=1):
        V[f"tc.j{i}"] = num(pay.get(k))
    V["tc.jsub1"] = sum(V[f"tc.j{i}"] for i in range(1, 6))
    V["tc.jsub2"] = V["tc.j6"] + V["tc.j7"]
    H = V["tc.H"] = num(tx["final_tax"]) if tx.get("final_tax") is not None else (V["tc.j2"] if sanchaya else 0)
    env = num(tx.get("environmental_surcharge"))
    delay = num(tx.get("delay_interest"))
    paid_given = opt(pay.get("paid_with_return"))

    life = inp.get("lifestyle", {})
    wl = inp.get("wealth", {})
    assets = wl.get("assets", {})
    liab = wl.get("liabilities", {})
    first_return = bool(tp.get("first_return"))
    prev = opt(wl.get("previous_net_wealth"))
    mode = wl.get("balancing_item") or ("gift" if prev is None else "cash")
    if mode not in ("cash", "gift", "none"):
        raise InputError("wealth.balancing_item must be 'cash', 'gift' or 'none'.")

    # Assets other than cash (fixed by the input).
    biz_present = bool(bz.get("balance_sheet"))
    V["a.agg"] = V["s4.r10"] if biz_present else num(assets.get("business_capital_aggregate"))
    V["a.bliab"] = V["s4.r15"] if biz_present else num(assets.get("business_liabilities"))
    V["a.bcap"] = V["a.agg"] - V["a.bliab"]
    V["a.dir"] = num(assets.get("director_shareholdings"))
    V["a.bcap_other"] = V["a.bcap"]
    items = assets.get("non_agricultural_property") or []
    if len(items) > 4:
        extra = items[3:]
        items = items[:3] + [{"description": f"Other {len(extra)} properties (see annexure)",
                              "value": sum(num(x.get("value")) for x in extra)}]
        W.append("More than 4 non-agricultural properties: lines 4+ were merged into one line; attach an annexure.")
    for i in range(4):
        it = items[i] if i < len(items) else None
        V[f"a.d{i + 1}_desc"] = str(it.get("description") or "") if it else ""
        V[f"a.d{i + 1}_val"] = num(it.get("value")) if it else None
    V["a.d_total"] = sum(num(x.get("value")) for x in (assets.get("non_agricultural_property") or []))
    agri = assets.get("agricultural_property") or []
    V["a.e_total"] = sum(num(x.get("value")) for x in agri)
    V["a.e_desc"] = "; ".join(str(x.get("description") or "") for x in agri if x.get("description"))
    for i, k in enumerate(("debenture_bond", "sanchayapatra_dps", "life_insurance", "loan_given", "fdr",
                           "provident_fund", "other_investment"), start=1):
        V[f"a.f{i}"] = num(assets.get(k))
    V["a.f_total"] = sum(V[f"a.f{i}"] for i in range(1, 8))
    V["a.g"] = num(assets.get("motor_car"))
    V["a.g_desc"] = str(assets.get("motor_car_details") or "")
    V["a.h"] = num(assets.get("ornaments"))
    V["a.h_qty"] = str(assets.get("ornaments_quantity") or "")
    V["a.h_type"] = str(assets.get("ornaments_type") if assets.get("ornaments_type") is not None else "(Gold)")
    V["a.h_note"] = str(assets.get("ornaments_note") or "")
    V["a.i"] = num(assets.get("furniture_electronics"))
    V["a.i_note"] = str(assets.get("furniture_note") or "")
    V["a.j"] = num(assets.get("other_assets"))
    non_cash = (V["a.bcap"] + V["a.dir"] + V["a.d_total"] + V["a.e_total"] + V["a.f_total"]
                + V["a.g"] + V["a.h"] + V["a.i"] + V["a.j"])
    V["w.6a"], V["w.6b"], V["w.6c"] = (num(liab.get(k)) for k in ("institutional", "non_institutional", "other"))
    V["w.liab"] = V["w.6a"] + V["w.6b"] + V["w.6c"]
    other_out = num(wl.get("other_outflows"))
    gift_in = num(wl.get("gift_and_other_receipts"))
    cash_in = num(assets.get("cash_bank"))
    life_amounts = {k: num(life.get(k)) for k in LIFESTYLE_ROWS if k != "tax_paid"}
    life_tax_override = opt(life.get("tax_paid"))
    surcharge_override = opt(tx.get("net_wealth_surcharge"))
    sc = R["surcharge"]

    def surcharge_for(net_wealth: float) -> int:
        if surcharge_override is not None:
            return int(surcharge_override)
        rate = 0.0
        for band in sc["bands"]:
            if band["upto"] is None or net_wealth <= band["upto"]:
                rate = band["rate"]
                break
        if tx.get("surcharge_trigger") and rate < sc["trigger_rate"]:
            rate = sc["trigger_rate"]  # more than one car / >8,000 sft house in a city corporation
        base = D if sc["base"] == "regular_tax" else F
        return rnd(base * rate)

    def settle(surcharge: int):
        """Payments, lifestyle total and net wealth for a given surcharge."""
        G = surcharge + env + delay
        I = F + G + H
        K = I - V["tc.jsub1"] - V["tc.jsub2"]
        p23 = paid_given if paid_given is not None else max(K, 0)
        p24 = V["tc.jsub1"] + V["tc.j7"] + V["tc.j6"] + p23
        life_tax = life_tax_override if life_tax_override is not None else p24
        life_total = sum(life_amounts.values()) + life_tax
        expenses = life_total + other_out
        if mode == "gift":
            net = non_cash + cash_in - V["w.liab"]
            gift = net + expenses - (prev or 0) - V["r11"] - V["r26"]
            cash = cash_in
        else:
            gift = gift_in
            net = V["r11"] + V["r26"] + gift + (prev or 0) - expenses
            cash = net + V["w.liab"] - non_cash if mode == "cash" else cash_in
        return G, I, K, p23, p24, life_tax, life_total, expenses, gift, net, cash

    # Net wealth sets the surcharge, and the surcharge (as tax paid, a lifestyle
    # expense) lowers net wealth, so look for a surcharge that agrees with itself.
    surcharge, seen = 0, set()
    for _ in range(6):
        G, I, K, p23, p24, life_tax, life_total, expenses, gift, net, cash = settle(surcharge)
        new = surcharge_for(net)
        if new == surcharge:
            break
        seen.update((surcharge, new))
        surcharge = new
    else:
        surcharge = max(seen)
        G, I, K, p23, p24, life_tax, life_total, expenses, gift, net, cash = settle(surcharge)
        W.append("Net wealth sits on a surcharge band edge (the surcharge itself moves it across); "
                 "the higher surcharge was used. Check return line 17.")

    V["tc.gs"] = surcharge + env
    V["tc.gd"] = delay
    V["tc.G"] = G
    V["tc.I"] = I
    V["tc.K"] = K
    V["tc.paid"] = paid_given if paid_given is not None else 0
    V["tc.challan"] = str(pay.get("challan_number") or "")
    V["tc.net"] = K - V["tc.paid"]

    # Return page 2-3 tax figures.
    V["r12"], V["r13"], V["r14"], V["r15"], V["r16"] = B, C_used, D, E, F
    V["r17a"], V["r17b"] = surcharge, env
    V["r17"] = surcharge + env
    V["r18"] = delay + H
    V["r19"] = F + V["r17"] + V["r18"]
    V["r20"], V["r21"], V["r22"] = V["tc.jsub1"], V["tc.j7"], V["tc.j6"]
    V["r22_years"] = str(pay.get("refund_assessment_years") or "")
    V["r23"] = p23
    V["r24"] = p24
    V["r25"] = V["r19"] - p24
    V["ack.income"], V["ack.paid"] = V["r11"], p24
    if V["r25"] > 0:
        W.append(f"Deficit of Tk {V['r25']:,.0f}: payments are less than the tax payable.")
    elif V["r25"] < 0:
        W.append(f"Excess payment of Tk {-V['r25']:,.0f} (refundable).")

    # IT-10BB lifestyle.
    comments = life.get("comments", {})
    for i, k in enumerate(LIFESTYLE_ROWS, start=1):
        V[f"lb.r{i}"] = life_tax if k == "tax_paid" else life_amounts[k]
        V[f"lb.c{i}"] = str(comments.get(k) or "")
    V["lb.total"] = V["lb.total2"] = life_total

    # IT-10B statement.
    V["w.1a"], V["w.1b"], V["w.1c"] = V["r11"], V["r26"], gift
    V["w.gift_label"] = str(wl.get("gift_label") if wl.get("gift_label") is not None
                            else ("(First Return)" if first_return else ""))
    V["w.src"] = V["w.1a"] + V["w.1b"] + V["w.1c"]
    V["w.2"] = prev
    V["w.3"] = V["w.src"] + (prev or 0)
    V["w.4a"], V["w.4b"] = life_total, other_out
    V["w.exp"] = expenses
    V["w.5"] = V["w.3"] - V["w.exp"]
    V["w.7"] = V["w.5"] + V["w.liab"]
    V["a.k"] = cash
    V["a.total"] = non_cash + cash
    if mode == "gift" and gift < 0:
        W.append(f"Balancing figure 'Receipt of gift and others' is negative ({gift:,.0f}): the listed assets "
                 "are smaller than income + previous wealth - expenses. Check the assets or expenses.")
    if mode == "cash" and cash < 0:
        W.append(f"Balancing figure 'Cash, bank and fund' is negative ({cash:,.0f}): expenses and assets exceed "
                 "the sources of fund. Add a source (gift, loan) or check the figures.")
    if abs(V["a.total"] - V["w.7"]) >= 1:
        W.append(f"IT-10B does not balance: total assets {V['a.total']:,.0f} vs gross wealth {V['w.7']:,.0f} "
                 f"(difference {V['a.total'] - V['w.7']:,.0f}).")

    V["age"] = age
    V["categories"] = cats
    return V, W
