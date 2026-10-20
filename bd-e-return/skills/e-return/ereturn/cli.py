"""Command line: python -m ereturn INPUT.json [-o OUT.pdf] [--summary-json FILE]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .calc import InputError, compute


def summary_lines(V: dict) -> list[str]:
    def tk(k):
        v = V.get(k)
        return "-" if v in (None, 0) else f"{v:,.0f}"

    return [
        f"Taxpayer          : {V['name']} (TIN {V['tin']}), AY {V['ay']}, rules '{V['rules_profile']}'",
        f"Tax-free threshold: {V['threshold']:,} ({', '.join(V['categories'])})",
        f"Total income      : {tk('r11')}   (salary {tk('r1')}, rent {tk('r2')}, other {V['r11'] - V['r1'] - V['r2']:,.0f})",
        f"Tax-exempt income : {tk('r26')}",
        f"Gross tax (slabs) : {tk('r12')}   rebate {tk('r13')}   minimum tax {tk('r15')}",
        f"Tax payable       : {tk('r16')}   surcharge {tk('r17')}   other {tk('r18')}   TOTAL {tk('r19')}",
        f"Paid / adjusted   : {tk('r24')}   (TDS {tk('r20')}, advance {tk('r21')}, refund adj {tk('r22')}, "
        f"with return {tk('r23')})   deficit/(excess) {tk('r25')}",
        f"Lifestyle expense : {tk('lb.total')}   net wealth {tk('w.5')}   gross wealth {tk('w.7')}",
        f"Balancing figure  : gift/other receipts {tk('w.1c')}, cash & bank {tk('a.k')}",
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m ereturn",
                                 description="Compute a Bangladesh individual return and print the 12-page PDF.")
    ap.add_argument("input", help="input JSON (see docs/INPUT.md)")
    ap.add_argument("-o", "--output", help="PDF to write (default: <input>.pdf)")
    ap.add_argument("--profile", help="override rules_profile (sample-template, ay2026-27, fo2025)")
    ap.add_argument("--summary-json", help="also write every computed figure to this JSON file")
    ap.add_argument("--no-pdf", action="store_true", help="only compute and print the summary")
    a = ap.parse_args(argv)

    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    if a.profile:
        data["rules_profile"] = a.profile
    try:
        V, warnings = compute(data)
    except InputError as e:
        print(f"INPUT ERROR: {e}", file=sys.stderr)
        return 2

    print("\n".join(summary_lines(V)))
    for w in warnings:
        print(f"WARNING: {w}")
    if a.summary_json:
        Path(a.summary_json).write_text(json.dumps(V, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    if not a.no_pdf:
        from .fonts import Fonts
        from .render import Renderer

        out = a.output or str(Path(a.input).with_suffix(".pdf"))
        fonts = Fonts()
        Renderer(fonts).render(V, out, title=f"Return of Income - {V['name']} - AY {V['ay']}")
        print(f"PDF written       : {out}")
        print(f"Fonts             : {fonts.report()}")
    return 0
