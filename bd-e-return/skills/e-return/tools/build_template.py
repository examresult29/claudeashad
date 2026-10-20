"""Build ereturn/template.json (the blank 12-page form) from a filled sample return.

Usage:
    python tools/build_template.py SAMPLE.pdf [--forbid "Name" --forbid 1234...]

Every word of the sample is kept as a form label unless it sits where a field in
ereturn/fields.py prints data; those words are dropped. Lines, boxes, shading and
the emblem position are copied as they are. --forbid strings must not survive
(use it with the taxpayer's name, NID, TIN, address) so no personal data can
leak into the template.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ereturn.fields import PAGES, masks  # noqa: E402

FONT_ROLES = {
    "Times New Roman": "serif", "Times New Roman,Bold": "serif-bold",
    "Calibri": "calibri", "Calibri,Bold": "calibri-bold",
    "Helvetica": "sans", "Helvetica-Bold": "sans-bold", "Arial": "sans", "Arial,Bold": "sans-bold",
    "Tahoma": "taka", "MS Gothic": "symbol",
}


def role(fontname: str) -> str:
    name = fontname.split("+", 1)[-1]
    if name not in FONT_ROLES:
        raise SystemExit(f"Unmapped font {fontname}")
    return FONT_ROLES[name]


def color(c):
    if c is None:
        return [0.0]
    if isinstance(c, (int, float)):
        return [round(float(c), 3)]
    return [round(float(x), 3) for x in c]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sample")
    ap.add_argument("--out", default=str(ROOT / "ereturn" / "template.json"))
    ap.add_argument("--forbid", action="append", default=[])
    a = ap.parse_args()

    pdf = pdfplumber.open(a.sample)
    if len(pdf.pages) != len(PAGES):
        raise SystemExit(f"Expected {len(PAGES)} pages, got {len(pdf.pages)}")
    out = {"width": float(pdf.pages[0].width), "height": float(pdf.pages[0].height), "pages": []}
    dropped = 0
    for page, fields in zip(pdf.pages, PAGES):
        H = float(page.height)
        regions = [m for f in fields for m in masks(f)]
        words = []
        for w in page.extract_words(extra_attrs=["fontname", "size", "non_stroking_color"],
                                    x_tolerance=1.5, return_chars=True):
            text = w["text"].replace("(cid:10)", "").replace("️", "")
            if not text.strip():
                continue
            base = H - w["chars"][0]["matrix"][5]
            cx = (w["x0"] + w["x1"]) / 2
            if any(x0 <= cx <= x1 and lo <= base <= hi for x0, x1, lo, hi in regions):
                dropped += 1
                continue
            words.append({"t": text, "font": role(w["fontname"]), "size": round(float(w["size"]), 2),
                          "c": color(w["non_stroking_color"]), "x": round(float(w["x0"]), 2),
                          "base": round(base, 2)})
        rects = [{"x0": round(r["x0"], 2), "top": round(r["top"], 2), "x1": round(r["x1"], 2),
                  "bot": round(r["bottom"], 2), "fill": color(r.get("non_stroking_color"))}
                 for r in page.rects if r.get("fill")]
        lines = [{"x0": round(ln["x0"], 2), "top": round(ln["top"], 2), "x1": round(ln["x1"], 2),
                  "bot": round(ln["bottom"], 2), "lw": round(float(ln.get("linewidth") or 0.1), 2),
                  "color": color(ln.get("stroking_color"))}
                 for ln in page.lines]
        images = [{"x0": round(i["x0"], 2), "top": round(i["top"], 2), "x1": round(i["x1"], 2),
                   "bot": round(i["bottom"], 2)} for i in page.images]
        out["pages"].append({"words": words, "rects": rects, "lines": lines, "images": images})

    blob = json.dumps(out, ensure_ascii=False)
    leaks = [s for s in a.forbid if s and s.lower() in blob.lower()]
    if leaks:
        raise SystemExit(f"Personal data still in template: {leaks}")
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kept = sum(len(p["words"]) for p in out["pages"])
    print(f"template written: {a.out} ({kept} label words kept, {dropped} data words dropped)")


if __name__ == "__main__":
    main()
