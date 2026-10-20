"""Tests for the calculation engine and PDF output.

Run with:  python3 tests/test_engine.py      (or: python3 -m pytest tests)
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ereturn.calc import compute  # noqa: E402

SAMPLE = json.loads((ROOT / "examples" / "sample-reproduction.json").read_text(encoding="utf-8"))
PRIVATE = json.loads((ROOT / "examples" / "private-employee.json").read_text(encoding="utf-8"))


def check(V, expected):
    bad = {k: (V[k], v) for k, v in expected.items() if round(V[k]) != v}
    assert not bad, f"mismatches (got, expected): {bad}"


def test_sample_pdf_figures():
    """Every figure printed on the sample return is reproduced."""
    V, _ = compute(SAMPLE)
    check(V, {
        # IT-11GA page 2
        "r1": 515808, "r2": 296250, "r3": 0, "r4": 0, "r5": 0, "r6": 0, "r7": 0, "r8": 0, "r9": 0,
        "r10": 0, "r11": 812058, "r12": 36206, "r13": 0, "r14": 36206, "r15": 5000, "r16": 36206,
        "r17": 0, "r18": 0, "r19": 36206,
        # page 3
        "r20": 0, "r21": 0, "r22": 0, "r23": 36206, "r24": 36206, "r25": 0, "r26": 5308,
        # acknowledgement
        "ack.income": 812058, "ack.paid": 36206,
        # Schedule 1 and 2
        "s1a.inc": 521116, "s1a.exm": 5308, "s1a.tax": 515808,
        "s2.r1": 395000, "s2.r6": 395000, "s2.da": 98750, "s2.r8": 98750, "s2.r9": 296250,
        # tax computation sheet
        "tc.A": 812058, "tc.An": 812058, "tc.s0.inc": 400000, "tc.s1.inc": 100000, "tc.s2.inc": 312058,
        "tc.s1.tax": 5000, "tc.s2.tax": 31206, "tc.B": 36206, "tc.ci": 24362, "tc.cii": 0,
        "tc.ciii": 1000000, "tc.C": 0, "tc.D": 36206, "tc.ei": 5000, "tc.E": 5000, "tc.F": 36206,
        "tc.G": 0, "tc.H": 0, "tc.I": 36206, "tc.K": 36206, "tc.paid": 0, "tc.net": 36206,
        # IT-10BB
        "lb.r1": 200000, "lb.r8": 36206, "lb.total": 236206,
        # IT-10B
        "w.1a": 812058, "w.1b": 5308, "w.1c": 14882682, "w.src": 15700048, "w.3": 15700048,
        "w.4a": 236206, "w.exp": 236206, "w.5": 15463842, "w.liab": 0, "w.7": 15463842,
        "a.d_total": 13400000, "a.f_total": 950048, "a.i": 300000, "a.k": 813794, "a.total": 15463842,
        # tax-free income sheet
        "tf.r01": 5308, "tf.total": 5308,
    })
    assert V["tc.s1.rate"] == "5%" and V["tc.s5.rate"] == "25%"
    assert V["w.gift_label"] == "(First Return)"
    assert V["iy_end_mdy"] == "6/30/2026" and V["iy_end_dmy"] == "30-Jun-26"


def test_same_person_under_current_rules():
    data = copy.deepcopy(SAMPLE)
    data["rules_profile"] = "ay2026-27"
    V, _ = compute(data)
    # women's threshold 4,50,000: 3,00,000 @10% + 62,058 @15% = 39,308.7
    check(V, {"threshold": 450000, "tc.B": 39309, "r19": 39309, "lb.total": 239309, "w.1c": 14885785})


def test_private_salary_exemption_and_rebate():
    V, _ = compute(PRIVATE)
    check(V, {"s1b.total": 1284000, "s1b.exempt": 428000, "r1": 856000, "r2": 172500, "r6": 80200,
              "r11": 1108700, "tc.An": 1053500, "tc.B": 83025, "tc.C": 31605, "tc.F": 51420,
              "tc.H": 5520, "r19": 56940, "r20": 56020, "r23": 920, "r25": 0, "a.k": 193760})
    data = copy.deepcopy(PRIVATE)
    data["salary"]["private"] = {"basic_pay": 2400000}
    V, _ = compute(data)
    assert V["s1b.exempt"] == 500000  # capped


def test_below_threshold_pays_nothing():
    data = copy.deepcopy(PRIVATE)
    data.update(house_property=[], other_income={}, investments={}, payments={})
    data["salary"]["private"] = {"basic_pay": 450000}  # 1/3 exempt -> 3,00,000 taxable
    V, _ = compute(data)
    check(V, {"r11": 300000, "tc.B": 0, "tc.E": 0, "r19": 0})


def test_minimum_tax_and_first_return():
    data = copy.deepcopy(PRIVATE)
    data.update(house_property=[], other_income={}, investments={}, payments={})
    data["salary"]["private"] = {"basic_pay": 630000}  # 4,20,000 taxable -> 2,000 slab tax
    V, _ = compute(data)
    check(V, {"tc.B": 2000, "tc.E": 5000, "r16": 5000})
    data["taxpayer"]["first_return"] = True
    V, _ = compute(data)
    check(V, {"tc.E": 1000, "r16": 2000})


def test_refund_when_tds_exceeds_tax():
    data = copy.deepcopy(PRIVATE)
    data["payments"]["tds_salary"] = 60000
    V, warnings = compute(data)
    assert V["tc.K"] < 0 and V["r23"] == 0 and V["r25"] == V["tc.K"]
    assert any("refundable" in w for w in warnings)


def test_net_wealth_surcharge():
    data = copy.deepcopy(PRIVATE)
    data["wealth"]["previous_net_wealth"] = 60000000  # 6 crore -> 10% band
    V, _ = compute(data)
    assert 40000000 < V["w.5"] <= 100000000
    # ay2026-27 levies it on the regular tax (D), not the minimum tax
    assert V["r17a"] == round(V["tc.D"] * 0.10)
    assert V["r19"] == V["r16"] + V["r17"] + V["r18"]


def test_surcharge_band_edge_is_consistent():
    """Net wealth just over Tk 4 crore before the surcharge, under it after."""
    data = copy.deepcopy(PRIVATE)
    data["wealth"]["previous_net_wealth"] = 39377240  # net wealth 4,00,01,000 with no surcharge
    V, warnings = compute(data)
    assert any("band edge" in w for w in warnings)
    assert V["r17a"] == round(V["tc.D"] * 0.10)
    assert V["r19"] == V["r16"] + V["r17"] + V["r18"] and V["r24"] == V["lb.r8"]
    assert V["a.total"] == V["w.7"]


def test_partial_ownership_and_commercial_rate():
    data = copy.deepcopy(PRIVATE)
    data["house_property"] = [{"annual_value": 600000, "type": "commercial", "ownership_share": 0.5}]
    V, _ = compute(data)
    check(V, {"s2.da": 180000, "s2.r9": 420000, "s2.r10": 210000, "r2": 210000})
    assert V["s2.rate"] == "30%"


def test_pdf_has_twelve_pages():
    from pypdf import PdfReader

    from ereturn.render import Renderer

    V, _ = compute(SAMPLE)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "r.pdf"
        Renderer().render(V, str(out))
        reader = PdfReader(str(out))
        assert len(reader.pages) == 12
        text = reader.pages[2].extract_text()
        assert "812,058" in text and "36,206" in text and "Sample Taxpayer" in text


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failed else 0)
