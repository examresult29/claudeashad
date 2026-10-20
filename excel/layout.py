"""Turn one page of the measured return layout into an Excel grid.

Every border line, shaded box and text position of the page becomes a column or
row boundary, so labels start where the sample's do, numbers end where the
sample's do, and borders fall on cell edges. Printed on A4 at the page's scale with
the margins set from the page, the sheet reproduces the page.

Positions are in points on the printed page. A page printed at a scale s (the sample
shrank some pages to 84% or 90%) is laid out at 1/s in the sheet, so its fonts keep
their true sizes; cell paddings and the pixel grid are the sheet's, hence times s on paper.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PADL = 1.8   # Excel's left indent of text inside a cell (pt, at 100%)
PADR = 1.8   # right indent
PX = 96 / 72  # Excel lays out columns and rows on a 96-dpi pixel grid

FONT_DESC = {"serif": 0.216, "serif-bold": 0.216, "calibri": 0.25, "calibri-bold": 0.25,
             "sans": 0.212, "sans-bold": 0.212, "taka": 0.21, "symbol": 0.14}


def text_bottom(base: float, size: float, role: str, s: float = 1.0) -> float:
    """Row bottom that puts a bottom-aligned text's baseline at `base`."""
    return base + FONT_DESC.get(role, 0.22) * size + 0.9 * s


@dataclass
class Item:
    """Something written into a cell: a label, a formula, a tick..."""
    x: float               # left edge (align l, d), right anchor (r) or centre (c)
    base: float
    size: float
    role: str
    align: str = "l"       # l | r | c | d (distributed: spread from x to x + width)
    width: float = 0.0     # expected text width, used for merges
    value: str = ""
    color: tuple = (0, 0, 0)
    kind: str = "text"     # text | amount | check
    cond_bold: str | None = None
    wrap_lines: int = 1
    lead: float = 0.0
    underline: bool = False
    rich: list | None = None    # [(text, role, color)] when touching runs share the cell
    right: float | None = None  # amounts: where the sample's digits end ...
    dash: float | None = None   # ... and where its zero dash ends
    # filled in by Grid.place()
    row: int = -1
    col: int = -1
    rows: tuple = ()
    cols: tuple = ()


@dataclass
class Grid:
    xs: list = field(default_factory=list)   # column boundaries (pt)
    ys: list = field(default_factory=list)   # row boundaries (pt)
    hsegs: list = field(default_factory=list)
    vsegs: list = field(default_factory=list)
    fills: list = field(default_factory=list)
    images: list = field(default_factory=list)
    items: list = field(default_factory=list)
    problems: list = field(default_factory=list)
    scale: float = 1.0


def cluster(points, tol):
    """points: [(value, strong)] -> sorted boundary values; strong points (lines) win."""
    points = sorted(points)
    groups, cur = [], []
    for v, strong in points:
        if cur and v - cur[-1][0] > tol:
            groups.append(cur)
            cur = []
        cur.append((v, strong))
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        strong = [v for v, s in g if s]
        pick = strong if strong else [v for v, _ in g]
        out.append(sum(pick) / len(pick))
    return out


def nearest(bounds, v):
    best = min(range(len(bounds)), key=lambda i: abs(bounds[i] - v))
    return best


def build_grid(page: dict, items: list[Item], width: float, height: float, scale: float = 1.0) -> Grid:
    g = Grid(items=items, scale=scale)
    padl, padr = PADL * scale, PADR * scale
    for r in page["rects"]:
        w, h = r["x1"] - r["x0"], r["bot"] - r["top"]
        if h <= 2.5 and (w >= h or w <= 2.5):  # dots of a dotted rule count as horizontal
            g.hsegs.append(((r["top"] + r["bot"]) / 2, r["x0"], r["x1"], h))
        elif w <= 2.5 and h > w:
            g.vsegs.append(((r["x0"] + r["x1"]) / 2, r["top"], r["bot"], w))
        else:
            g.fills.append((r["x0"], r["top"], r["x1"], r["bot"], r["fill"]))
    g.images = list(page["images"])

    # A dotted rule comes as a row of short dashes: make it one dotted border (lw -2).
    dashes = sorted((h for h in g.hsegs if h[2] - h[1] < 6), key=lambda h: (round(h[0]), h[1]))
    rows, rest = [], [h for h in g.hsegs if h[2] - h[1] >= 6]
    for h in dashes:
        if rows and abs(h[0] - rows[-1][-1][0]) < 0.5 and h[1] - rows[-1][-1][2] < 4:
            rows[-1].append(h)
        else:
            rows.append([h])
    for row in rows:
        if len(row) >= 5:
            rest.append((sum(h[0] for h in row) / len(row), row[0][1], row[-1][2], -2.0))
        else:
            rest += row
    g.hsegs = rest

    # Double underlines: two horizontal lines about 2pt apart become one "double" border.
    hs = sorted(g.hsegs)
    used = [False] * len(hs)
    merged = []
    for i, a in enumerate(hs):
        if used[i]:
            continue
        used[i] = True
        partner = None
        for j in range(i + 1, len(hs)):
            b = hs[j]
            if b[0] - a[0] > 3.2:
                break
            if (not used[j] and a[3] > 0 and b[3] > 0 and abs(b[1] - a[1]) < 2 and abs(b[2] - a[2]) < 2
                    and b[0] - a[0] > 1.2):
                partner = j
                break
        if partner is None:
            merged.append(a)
        else:
            used[partner] = True
            b = hs[partner]
            merged.append(((a[0] + b[0]) / 2, min(a[1], b[1]), max(a[2], b[2]), -1.0))  # -1 = double
    # A rule just under a label and exactly as long is the label's underline, not a border; so is
    # one under a field that starts with it and fits its slot (the sample underlined a date).
    g.hsegs = []
    for y, x0, x1, lw in merged:
        under = [it for it in items if lw > 0 and it.kind == "text" and it.wrap_lines == 1
                 and it.align == "l" and it.base < y < it.base + 0.4 * it.size and abs(x0 - it.x) < 3
                 and (x1 - x0 <= it.width + 4 if it.value.startswith("=") else abs(x1 - (it.x + it.width)) < 4)]
        if under:
            under[0].underline = True
        else:
            g.hsegs.append((y, x0, x1, lw))

    # A number that ends a hair left of a box edge, or of the rule under it, belongs to the cell
    # that ends there.
    for it in items:
        if it.align == "r" and it.wrap_lines == 1:
            t = it.x + padr
            ends = [x for x, y0, y1, lw in g.vsegs if t - 3.5 <= x <= t + 1.0 and y0 - 1 <= it.base <= y1 + 1]
            if not ends and it.kind == "amount":
                ends = [x1 for y, x0, x1, lw in g.hsegs
                        if it.base < y <= it.base + 0.6 * it.size + 1 and t - 5.0 <= x1 <= t + 1.0 and x0 < x1 - it.size]
            if ends:
                it.x = min(ends, key=lambda x: abs(x - t)) - padr

    xp, yp, text_bottoms = [], [], []
    for x, y0, y1, lw in g.vsegs:
        xp.append((x, True))
        yp += [(y0, True), (y1, True)]
    for y, x0, x1, lw in g.hsegs:
        yp.append((y, True))
        xp += [(x0, True), (x1, True)]
    for x0, top, x1, bot, _ in g.fills:
        xp += [(x0, False), (x1, False)]
        yp += [(top, False), (bot, False)]
    for im in g.images:
        yp.append((im["top"], False))
    for it in items:
        if it.wrap_lines > 1:
            # A wrapped block: top of the first line to the bottom of the last.
            yp += [(it.base - it.size, False),
                   (text_bottom(it.base + (it.wrap_lines - 1) * it.lead, it.size, it.role, scale), False)]
            xp += [(it.x - padl, False), (it.x + it.width, False)]
            continue
        text_bottoms.append((text_bottom(it.base, it.size, it.role, scale), it.size))
        if it.align == "d":
            xp += [(it.x - padl, False), (it.x + it.width + padr, False)]
        elif it.align == "l":
            xp.append((it.x - padl, False))
        elif it.align == "r":
            xp.append((it.x + padr, False))
            if it.kind == "amount":
                # Room for the widest number: up to the label before it, unless a box edge comes first.
                ends = [o.x + o.width if o.align == "l" else o.x if o.align == "r" else o.x + o.width / 2
                        for o in items if o.kind != "amount" and o.wrap_lines == 1
                        and abs(o.base - it.base) < 0.6 * max(o.size, it.size)]
                ends = [e for e in ends if e < it.x - 5]
                left = max([it.x + padr - 6.5 * it.size] + [e + 1.0 for e in ends])
                if not any(left < x < it.x for x, y0, y1, lw in g.vsegs if y0 - 1 <= it.base <= y1 + 1):
                    xp.append((left, False))
        else:
            xp += [(it.x - 1.0, False), (it.x + 1.0, False)]
    # Texts on one visual line often sit a point or two apart (different fonts and cells);
    # give them one row, kept where the largest text wants it, and let a text that ends just
    # above a border use that border instead of a sliver row.
    strong_y = sorted(v for v, strong in yp if strong)
    groups = []
    for bottom, size in sorted(text_bottoms):
        if groups and bottom - groups[-1][-1][0] <= 2.4:
            groups[-1].append((bottom, size))
        else:
            groups.append([(bottom, size)])
    for grp in groups:
        rep = max(grp, key=lambda t: t[1])[0]
        near = [y for y in strong_y if -1.0 <= y - rep <= 1.8]
        yp.append((near[0] if near else rep, False))
    lo_x = min(v for v, _ in xp) - 0.5
    hi_x = max([v for v, _ in xp] + [it.x + it.width for it in items if it.align == "l"]) + 1
    lo_y = min(v for v, _ in yp) - 14
    hi_y = max(v for v, _ in yp) + 2
    xp += [(max(lo_x, 0), False), (min(hi_x, width - 6), False)]
    yp += [(max(lo_y, 0), False), (min(hi_y, height - 6), False)]
    g.xs = snap(cluster(xp, 0.9), PX / scale)
    g.ys = snap(cluster(yp, 0.9), PX / scale)
    place(g)
    return g


def snap(bounds, px_per_pt):
    """Round boundaries onto the sheet's 96-dpi pixel grid (relative to the first) without drift."""
    out, last = [], None
    b0 = bounds[0]
    for b in bounds:
        px = round((b - b0) * px_per_pt)
        if last is not None and px <= last:
            continue
        out.append(b0 + px / px_per_pt)
        last = px
    return out


def place(g: Grid):
    hard = {}    # cells that hold an item
    claimed = {}  # empty cells a label's text runs on over
    padl, padr, s = PADL * g.scale, PADR * g.scale, g.scale
    ncol = len(g.xs) - 1

    def take(it, rows, cols):
        it.rows, it.cols = tuple(rows), tuple(cols)
        for r in rows:
            for c in cols:
                other = hard.get((r, c)) or claimed.get((r, c))
                if other is not None and other is not it:
                    g.problems.append(f"overlap at row {r} col {c}: {it.value!r} vs {other.value!r}")
                hard[(r, c)] = it

    def extent(it):
        if it.align in "ld":
            return it.x, it.x + it.width
        if it.align == "r":
            return it.x - it.width, it.x
        return it.x - it.width / 2, it.x + it.width / 2

    def claim(it):
        """A text in a single cell runs on over the empty cells it reaches; keep those free."""
        a, b = extent(it)
        for c in range(ncol):
            if g.xs[c] < b - 1.0 and g.xs[c + 1] > a + 1.0 and (it.row, c) not in hard:
                claimed.setdefault((it.row, c), it)

    growers = []
    for it in g.items:
        if it.wrap_lines > 1:
            top = nearest(g.ys, it.base - it.size)
            bot = nearest(g.ys, text_bottom(it.base + (it.wrap_lines - 1) * it.lead, it.size, it.role, s))
            left, right = nearest(g.xs, it.x - padl), nearest(g.xs, it.x + it.width)
            it.row, it.col = top, left
            take(it, range(top, bot), range(left, right))
            continue
        bottom = text_bottom(it.base, it.size, it.role, s)
        it.row = max(nearest(g.ys, bottom) - 1, 0)
        if it.align in "ld":
            it.col = nearest(g.xs, it.x - padl)
        elif it.align == "r":
            it.col = max(nearest(g.xs, it.x + padr) - 1, 0)
        else:
            it.col = nearest(g.xs, it.x - 1.0)
        # Too short for the text? Take in the empty rows above.
        top = it.row
        while g.ys[it.row + 1] - g.ys[top] < 0.78 * it.size and top > 0:
            top -= 1
        rows, cols = list(range(top, it.row + 1)), [it.col]
        if it.kind == "amount" or (it.kind == "text" and it.value.startswith("=") and it.align in "lr"):
            growers.append((it, rows))
            continue
        if it.align == "d":
            cols = list(range(it.col, max(nearest(g.xs, it.x + it.width + padr), it.col + 1)))
        elif len(rows) > 1:
            # Merged cells cannot spill into neighbours: widen.
            if it.align == "r":
                left = it.col
                while g.xs[it.col + 1] - g.xs[left] < it.width and left > 0:
                    left -= 1
                cols = list(range(left, it.col + 1))
            elif it.align == "l":
                right = it.col
                while g.xs[right + 1] - g.xs[it.col] < it.width and right < ncol - 1:
                    right += 1
                cols = list(range(it.col, right + 1))
            else:
                l, r = it.col, it.col
                while g.xs[r + 1] - g.xs[l] < it.width and (l > 0 or r < ncol - 1):
                    l, r = max(l - 1, 0), min(r + 1, ncol - 1)
                cols = list(range(l, r + 1))
        take(it, rows, cols)
    for it, rows in growers:  # hold every field's and number's own cell before any grows
        take(it, rows, [it.col])

    for it in g.items:
        if it.kind != "amount" and len(it.rows) == 1 and len(it.cols) == 1 and not it.value.startswith("="):
            a, b = extent(it)
            nxt = [c for c in range(it.col + 1, ncol) if (it.row, c) in hard]
            if it.align in "ld" and nxt and g.xs[nxt[0]] < b - 1.0:
                g.problems.append(f"{it.value!r} is cut off by {hard[(it.row, nxt[0])].value!r}")
            claim(it)

    # Fields and numbers get a merged cell of their own: a field as wide as its slot (its text
    # shrinks to fit, as on the PDF), a number with room to its left up to the nearest box edge
    # or label, since a number too wide for its cell prints as ###.
    vb, hb = set(), set()
    for x, y0, y1, lw in g.vsegs:
        ci = nearest(g.xs, x)
        for r in range(nearest(g.ys, y0), nearest(g.ys, y1)):
            vb.add((ci, r))
    for y, x0, x1, lw in g.hsegs:
        ri = nearest(g.ys, y)
        for c in range(nearest(g.xs, x0), nearest(g.xs, x1)):
            hb.add((ri, c))
    growers.sort(key=lambda t: t[0].kind == "amount")
    for it, rows in growers:
        top, bot = rows[0], rows[-1] + 1

        def free(c, edge):
            """Can the cell take in column c, crossing the column boundary `edge`? Not over a
            box edge or a rule inside it (merging would hide them), nor over another text."""
            return (0 <= c < ncol and not any((edge, r) in vb for r in rows)
                    and not any((r, c) in hard or (r, c) in claimed for r in rows)
                    and not any((r, c) in hb for r in range(top + 1, bot)))

        left = right = it.col
        a, b = extent(it)
        if it.kind == "amount":
            while g.xs[right + 1] - g.xs[left] < 6.5 * it.size and free(left - 1, left):
                left -= 1
            if g.xs[right + 1] - g.xs[left] < it.width:
                g.problems.append(f"narrow number cell ({g.xs[right + 1] - g.xs[left]:.0f}pt) for {it.value!r}")
        else:
            while it.align == "l" and g.xs[right + 1] < b - 0.5 and free(right + 1, right + 1):
                right += 1
            while it.align == "r" and g.xs[left] > a + 0.5 and free(left - 1, left):
                left -= 1
        take(it, rows, range(left, right + 1))
        if len(rows) == 1 and left == right:
            claim(it)
