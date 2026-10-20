"""Draw the 12-page return: the blank form template plus every computed value."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .fields import PAGES
from .fonts import Fonts

HERE = Path(__file__).parent
TEMPLATE = HERE / "template.json"
EMBLEM = HERE / "assets" / "emblem.png"


def fmt_amount(v: float) -> str:
    n = int(round(abs(v)))
    s = f"{n:,}"
    return f"({s})" if v < 0 else s


def _color(c, rgb):
    if rgb is None:
        c.setFillColorRGB(0, 0, 0)
    elif isinstance(rgb, (int, float)):
        c.setFillGray(rgb)
    elif len(rgb) == 1:
        c.setFillGray(rgb[0])
    elif len(rgb) == 3:
        c.setFillColorRGB(*rgb)
    elif len(rgb) == 4:
        c.setFillColorCMYK(*rgb)


class Renderer:
    def __init__(self, fonts: Fonts | None = None):
        self.fonts = fonts or Fonts()
        self.tpl = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.W, self.H = self.tpl["width"], self.tpl["height"]

    # ------------------------------------------------------------ helpers
    def y(self, top: float) -> float:
        return self.H - top

    def width(self, s: str, role: str, size: float) -> float:
        return stringWidth(s, self.fonts.get(role), size)

    def put(self, c, s: str, x: float, base: float, role: str, size: float, align="l", color=None):
        if not s:
            return
        font = self.fonts.get(role)
        c.setFont(font, size)
        _color(c, color)
        if align == "r":
            c.drawRightString(x, self.y(base), s)
        elif align == "c":
            c.drawCentredString(x, self.y(base), s)
        else:
            c.drawString(x, self.y(base), s)

    def tick(self, c, cx: float, base: float, size: float, at=None):
        """A heavy check mark; uses a font glyph when one is available."""
        c.setFillColorRGB(0, 0, 0)
        if self.fonts.has("symbol"):
            w = self.width("✔", "symbol", size)
            x = at[0] if at else cx - w / 2
            self.put(c, "✔", x, at[1] if at else base, "symbol", size)
            return
        x = (at[0] + size / 2) if at else cx
        b = at[1] if at else base
        c.setLineWidth(1.6)
        c.setStrokeColorRGB(0, 0, 0)
        p = c.beginPath()
        p.moveTo(x - 0.33 * size, self.y(b - 0.38 * size))
        p.lineTo(x - 0.10 * size, self.y(b - 0.08 * size))
        p.lineTo(x + 0.36 * size, self.y(b - 0.78 * size))
        c.drawPath(p, stroke=1, fill=0)

    # ------------------------------------------------------- static layer
    def draw_template(self, c, page: dict):
        for r in page["rects"]:
            _color(c, r["fill"])
            c.rect(r["x0"], self.y(r["bot"]), r["x1"] - r["x0"], r["bot"] - r["top"], stroke=0, fill=1)
        for ln in page["lines"]:
            col = ln.get("color")
            if isinstance(col, list) and len(col) == 3:
                c.setStrokeColorRGB(*col)
            else:
                c.setStrokeGray(col[0] if isinstance(col, list) else (col or 0))
            c.setLineWidth(ln["lw"])
            c.line(ln["x0"], self.y(ln["top"]), ln["x1"], self.y(ln["bot"]))
        for im in page["images"]:
            c.drawImage(str(EMBLEM), im["x0"], self.y(im["bot"]), im["x1"] - im["x0"], im["bot"] - im["top"])
        for w in page["words"]:
            role = w["font"]
            if role == "taka":
                if not self.fonts.has("taka"):
                    self.put(c, w["t"].replace("৳", "Tk"), w["x"], w["base"], "serif", w["size"], color=w["c"])
                    continue
                if "tahoma" not in self.fonts.files["taka"].lower():
                    # Other fonts draw the Taka sign smaller than Tahoma does.
                    self.put(c, w["t"], w["x"], w["base"], role, w["size"] * 1.35, color=w["c"])
                    continue
            self.put(c, w["t"], w["x"], w["base"], role, w["size"], color=w["c"])

    # ------------------------------------------------------- data layer
    def fit(self, s: str, role: str, size: float, maxw: float) -> float:
        """Shrink the font (down to 70%) until the text fits the box."""
        while size > 6 and self.width(s, role, size) > maxw:
            size -= 0.25
        return size

    def wrap(self, s: str, role: str, size: float, maxw: float) -> list[str]:
        lines, cur = [], ""
        for word in s.split():
            trial = f"{cur} {word}".strip()
            if self.width(trial, role, size) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def draw_text(self, c, f, s: str):
        s = str(s or "").strip()
        if not s:
            return
        role, size, maxw = f["font"], f["size"], f["maxw"]
        if f["lines"] > 1:
            lines = self.wrap(s, role, size, maxw)
            while len(lines) > f["lines"] and size > 6:
                size -= 0.25
                lines = self.wrap(s, role, size, maxw)
            for i, line in enumerate(lines[: f["lines"]]):
                self.put(c, line, f["x"], f["base"] + i * f["lead"], role, size, f["align"], f["color"])
            return
        size = self.fit(s, role, size, maxw)
        self.put(c, s, f["x"], f["base"], role, size, f["align"], f["color"])

    def draw_amount(self, c, f, v):
        if v is None:
            return
        role, size = f["font"], f["size"]
        if round(v) == 0:
            if f["zero"] == "blank":
                return
            digit = self.width("0", role, size)
            right = f["dash"] + 0.0 if f["dash"] else f["right"] - 2 * digit
            self.put(c, "-", right, f["base"], role, size, "r", f["color"])
            return
        s = fmt_amount(v)
        right = f["right"] + (self.width(")", role, size) if v < 0 else 0)
        self.put(c, s, right, f["base"], role, size, "r", f["color"])

    def draw_field(self, c, f, V):
        k = f["kind"]
        v = V.get(f["key"])
        if k == "text":
            self.draw_text(c, f, v)
        elif k == "amount":
            self.draw_amount(c, f, v)
        elif k == "digits":
            for ch, cx in zip(str(v or ""), f["centers"]):
                self.put(c, ch, cx, f["base"], f["font"], f["size"], "c")
        elif k == "check":
            if v:
                x0, top, x1, bot = f["box"]
                size = 10.56
                self.tick(c, (x0 + x1) / 2, bot - 3.6, size, f.get("at"))
        elif k == "relation":
            x, b, size = f["x"], f["base"], f["size"]
            if v == "husband":
                parts = [("Father/", "serif"), ("Husband", "serif-bold"), (",", "serif")]
            else:
                parts = [("Father", "serif-bold"), ("/Husband,", "serif")]
            for s, role in parts:
                self.put(c, s, x, b, role, size)
                x += self.width(s, role, size)
        elif k == "ornaments":
            qty, typ = str(V.get("a.h_qty") or ""), str(V.get("a.h_type") or "")
            x, b, size = f["x"], f["base"], f["size"]
            if qty:
                self.put(c, qty + " ", x, b, "serif-bold", size)
                x += self.width(qty + " ", "serif-bold", size)
            if qty or V.get("a.h"):
                self.put(c, typ, x, b, "serif", size)

    # ------------------------------------------------------------- output
    def render(self, V: dict, out_path: str, title: str = "Return of Income"):
        c = canvas.Canvas(str(out_path), pagesize=(self.W, self.H))
        c.setTitle(title)
        c.setAuthor(V.get("name", ""))
        c.setSubject(f"Return of income, assessment year {V.get('ay', '')}")
        c.setCreator("bd-e-return plugin")
        for page, fields in zip(self.tpl["pages"], PAGES):
            self.draw_template(c, page)
            for f in fields:
                self.draw_field(c, f, V)
            c.showPage()
        c.save()
        return out_path
