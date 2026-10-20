"""Where every computed value is printed on the 12 pages.

Coordinates are PDF points measured from the sample return (A4, 595.32 x 841.92),
with y given as the text baseline measured from the TOP of the page. Amount
fields are right-aligned at the edge where the sample's numbers end and print a
dash for zero (Excel accounting format) unless zero="blank".

The same definitions tell tools/build_template.py which words of the sample are
data (removed from the blank template) and which are form labels (kept).
"""
from __future__ import annotations

from .calc import GOVT_ROWS, LIFESTYLE_ROWS, PRIVATE_ROWS

S, SB, C, CB, A, AB = "serif", "serif-bold", "calibri", "calibri-bold", "sans", "sans-bold"


def text(key, x, base, font, size, align="l", maxw=200, lines=1, lead=None, color=None):
    return dict(kind="text", key=key, x=x, base=base, font=font, size=size, align=align,
                maxw=maxw, lines=lines, lead=lead or size * 1.2, color=color)


def amt(key, right, base, font, size, zero="dash", dash=None, color=None, maskw=60):
    return dict(kind="amount", key=key, right=right, base=base, font=font, size=size,
                zero=zero, dash=dash, color=color, maskw=maskw)


def digs(key, centers, base, font, size):
    return dict(kind="digits", key=key, centers=centers, base=base, font=font, size=size)


def check(key, box, at=None):
    return dict(kind="check", key=key, box=box, at=at)


def centers(x0s, size):
    """Box centres from the x0 of the sample's digits (digit width = size/2)."""
    return [round(x + size / 4, 2) for x in x0s]


# Text-box centres of the 12 TIN digits on each page.
TIN_P1 = [79.82, 103.10, 126.26, 144.86, 163.46, 182.06, 200.69, 219.29, 237.89, 256.49, 275.09, 293.69]
TIN_P2 = centers([142.22, 160.82, 179.42, 198.05, 216.65, 235.25, 253.85, 272.45, 291.05, 309.65, 328.27, 346.87], 10.56)
TIN_P3 = centers([328.27, 346.87, 365.47, 385.99, 406.51, 427.39, 449.14, 467.74, 486.34, 508.06, 529.66, 549.10], 10.56)
TIN_P4 = centers([100.46, 123.62, 142.22, 160.82, 179.42, 198.05, 216.65, 235.25, 253.85, 272.45, 291.05, 309.65], 10.56)
TIN_P5 = centers([260.33, 280.49, 300.65, 320.83, 340.99, 361.15, 381.31, 401.47, 421.63, 441.82, 461.98, 482.14], 11.04)
TIN_P6 = centers([258.65, 280.37, 302.09, 323.83, 345.55, 367.27, 388.99, 410.71, 432.43, 454.18, 475.90, 497.62], 11.04)
TIN_P7 = centers([280.37, 302.09, 323.83, 345.55, 367.27, 388.99, 410.71, 432.43, 454.18, 475.90, 497.62, 518.62], 11.04)
TIN_P7B = centers([236.93, 258.65, 280.37, 302.09, 323.83, 345.55, 367.27, 388.99, 410.71, 432.43, 454.18, 475.90], 11.04)
TIN_P9 = centers([258.41, 278.09, 299.33, 318.31, 335.11, 353.35, 370.99, 388.51, 407.11, 426.07, 442.66, 463.66], 9.24)
DOB_P2 = centers([58.56, 77.18, 123.62, 142.22, 179.42, 198.05, 216.65, 235.25], 10.56)

# ---------------------------------------------------------------- page 1
P1 = [  # IT-11 Chha acknowledgement receipt
    text("ay", 315.31, 280.61, SB, 11.52, maxw=120),
    text("name", 155.54, 322.37, SB, 10.56, maxw=400),
    text("nid", 322.99, 347.93, SB, 10.56, maxw=235),
    digs("tin", TIN_P1, 378.53, SB, 13.44),
    text("circle", 131.06, 408.29, SB, 10.56, maxw=90),
    text("zone", 325.39, 408.29, SB, 10.56, maxw=230),
    amt("ack.income", 277.37, 458.11, SB, 13.44, maskw=70),
    amt("ack.paid", 277.37, 489.43, SB, 13.44, maskw=70),
]

# ---------------------------------------------------------------- page 2
P2 = [  # IT-11GA page 1: identity
    text("name", 174.14, 198.98, SB, 10.56, maxw=385),
    text("nid", 341.59, 229.46, SB, 10.56, maxw=218),
    digs("tin", TIN_P2, 261.74, SB, 10.56),
    text("circle", 136.94, 291.53, SB, 10.56, maxw=125),
    text("zone", 344.23, 291.53, SB, 10.56, maxw=215),
    text("ay", 174.14, 320.33, SB, 10.56, maxw=95),
    check("resident", (417.55, 309.53, 442.65, 324.41), at=(421.15, 320.21)),
    check("nonresident", (522.10, 309.53, 541.66, 324.41)),
    check("box.ff", (246.29, 379.13, 265.85, 394.01)),
    check("box.female", (320.71, 379.13, 340.27, 394.01)),
    check("box.third", (417.55, 379.13, 441.69, 394.01)),
    check("box.disabled", (522.10, 379.13, 541.66, 394.01)),
    check("box.65", (246.29, 400.49, 265.85, 415.37)),
    check("box.parent", (522.10, 400.49, 541.66, 415.37)),
    digs("dob_digits", DOB_P2, 460.39, SB, 10.56),
    text("spouse_name", 401.5, 439.49, SB, 10.56, maxw=158),
    text("spouse_tin", 443.5, 460.27, SB, 10.56, maxw=116),
    text("address", 120.98, 488.71, SB, 10.56, maxw=438, lines=3, lead=13.0),
    text("telephone", 137.5, 533.83, SB, 10.56, maxw=126),
    text("mobile", 323.5, 533.83, SB, 10.56, maxw=116),
    text("email", 118.5, 550.99, SB, 10.56, maxw=145),
    text("employer", 306.83, 605.47, SB, 10.56, align="c", maxw=500),
    text("organization", 193.0, 634.06, SB, 10.56, maxw=366),
    text("bin", 249.0, 655.42, SB, 10.56, maxw=310),
    text("partners", 54.0, 697.5, S, 10.56, maxw=505, lines=3, lead=12.5),
]

# ---------------------------------------------------------------- page 3
P3 = [  # IT-11GA page 2: total income and tax computation
    text("iy_end_mdy", 438.91, 100.58, SB, 10.56, maxw=90),
    text("name", 155.54, 120.38, SB, 10.56, maxw=400),
    digs("tin", TIN_P3, 136.94, SB, 10.56),
] + [
    amt(f"r{i}", 556.06, base, S, 10.56, zero="blank" if i == 7 else "dash")
    for i, base in zip(range(1, 12), (192.98, 215.06, 237.14, 259.22, 281.33, 303.41, 325.49,
                                      347.57, 369.65, 391.73, 413.81))
] + [
    amt("r12", 556.06, 470.23, S, 10.56),
    amt("r13", 556.06, 492.31, S, 10.56),
    amt("r14", 556.06, 514.39, S, 10.56),
    amt("r15", 556.06, 536.47, S, 10.56),
    amt("r16", 556.06, 558.55, S, 10.56),
    amt("r17a", 455.35, 580.63, S, 10.56),
    amt("r17b", 455.35, 602.71, S, 10.56, zero="blank"),
    amt("r17", 556.06, 591.67, S, 10.56),
    amt("r18", 556.06, 624.82, S, 10.56),
    amt("r19", 556.06, 647.02, SB, 10.56),
]

# ---------------------------------------------------------------- page 4
P4 = [  # IT-11GA page 3: payments, documents, verification
    amt("r20", 455.35, 135.74, S, 10.56),
    amt("r21", 455.35, 155.78, S, 10.56),
    amt("r22", 455.35, 175.82, S, 10.56),
    text("r22_years", 464.0, 175.82, S, 9.0, maxw=95),
    amt("r23", 455.35, 195.86, S, 10.56),
    amt("r24", 455.35, 216.14, SB, 10.56),
    amt("r25", 455.35, 235.94, S, 10.56),
    amt("r26", 556.06, 276.05, S, 10.56),
] + [
    text(f"doc{i}", 174.14, base, S, 10.56, maxw=370)
    for i, base in zip(range(1, 8), (328.37, 342.29, 356.21, 370.13, 384.05, 397.97, 411.89))
] + [
    text("name", 71.90, 504.31, SB, 10.56, maxw=400),
    dict(kind="relation", key="relation", x=53.28, base=528.19, size=10.56),
    text("father_or_husband", 155.54, 527.83, SB, 10.56, maxw=400),
    digs("tin", TIN_P4, 553.15, SB, 10.56),
    text("place", 90.50, 687.22, S, 10.56, maxw=200),
    text("date", 90.50, 704.14, S, 10.56, maxw=150),
    text("name", 451.03, 704.38, SB, 10.56, align="c", maxw=210),
]

# ---------------------------------------------------------------- page 5
S1A_BASES = (158.18, 180.38, 202.58, 219.98, 237.38, 254.78, 272.21, 289.61,
             307.01, 324.41, 341.81, 359.21, 376.61, 394.01, 411.41, 428.81)
S1B_BASES = (518.23, 535.63, 553.03, 570.43, 587.83, 605.23, 622.63, 640.06,
             657.46, 674.86, 692.26, 709.66)
P5 = [  # Schedule 1: salaries
    text("name", 173.78, 94.58, SB, 11.04, maxw=330),
    digs("tin", TIN_P5, 109.58, SB, 11.04),
]
for _k, _b in zip(GOVT_ROWS, S1A_BASES):
    P5 += [amt(f"s1a.{_k}.inc", 347.96, _b, C, 11.04),
           amt(f"s1a.{_k}.exm", 428.64, _b, C, 11.04),
           amt(f"s1a.{_k}.tax", 509.29, _b, C, 11.04)]
P5 += [
    amt("s1a.inc", 347.84, 446.23, CB, 11.04),
    amt("s1a.exm", 428.52, 446.23, CB, 11.04),
    amt("s1a.tax", 509.17, 446.23, CB, 11.04),
]
for _i, (_k, _b) in enumerate(zip(PRIVATE_ROWS, S1B_BASES)):
    P5.append(amt(f"s1b.{_k}", 428.64, _b, C, 11.04, zero="dash" if _i < 2 else "blank"))
P5 += [
    amt("s1b.sub", 509.31, 613.87, C, 11.04),
    amt("s1b.total", 509.19, 727.06, CB, 11.04),
    amt("s1b.exempt", 509.31, 744.46, C, 11.04),
    amt("s1b.net", 509.31, 761.86, C, 11.04),
]

# ---------------------------------------------------------------- page 6
P6 = [  # Schedule 2 (house property) and Schedule 3 (agriculture)
    text("name", 165.14, 108.86, SB, 11.04, maxw=300),
    digs("tin", TIN_P6, 123.86, SB, 11.04),
    text("s2.desc", 36.5, 183.0, S, 9.0, maxw=100, lines=19, lead=11.0),
    amt("s2.r1", 483.46, 182.66, S, 11.04),
    amt("s2.r2", 483.46, 197.18, S, 11.04, zero="blank"),
    amt("s2.r3", 483.46, 211.70, S, 11.04, zero="blank"),
    amt("s2.r4", 483.46, 226.22, S, 11.04, zero="blank"),
    amt("s2.r5", 483.46, 240.74, S, 11.04, zero="blank"),
    amt("s2.r6", 567.22, 255.26, S, 11.04),
    text("s2.rate", 314.99, 284.33, S, 11.04, align="r", maxw=22),
    amt("s2.da", 483.46, 284.33, S, 11.04),
    amt("s2.db", 483.46, 298.85, S, 11.04, zero="blank"),
    amt("s2.dc", 483.46, 313.37, S, 11.04, zero="blank"),
    amt("s2.dd", 483.46, 327.65, S, 11.04, zero="blank"),
    amt("s2.de", 483.46, 341.81, S, 11.04, zero="blank"),
    amt("s2.df", 483.46, 356.09, S, 11.04, zero="blank"),
    amt("s2.r7", 567.22, 312.77, S, 11.04),
    amt("s2.r8", 567.12, 370.37, A, 11.04),
    amt("s2.r9", 567.13, 384.89, A, 11.04),
    amt("s2.r10", 567.13, 399.41, A, 11.04, zero="blank"),
    text("name", 165.14, 472.15, SB, 11.04, maxw=300),
    digs("tin", TIN_P6, 487.15, SB, 11.04),
    text("s3.nature", 137.0, 515.95, S, 11.04, maxw=420),
    amt("s3.r1", 567.42, 558.19, S, 11.04),
    amt("s3.r2", 567.42, 572.11, S, 11.04),
    amt("s3.r3", 567.42, 593.23, S, 11.04),
    amt("s3.r4", 567.51, 614.71, C, 11.04),
]

# ---------------------------------------------------------------- page 7
S4_ROWS = ((218.42, S), (232.34, S), (246.26, S), (260.18, S), (274.37, CB), (317.09, S), (331.01, S),
           (344.93, S), (358.85, S), (373.01, SB), (386.69, S), (400.61, S), (414.53, S), (428.69, C),
           (443.21, S), (457.75, CB))
S5_BASES = (596.95, 610.99, 624.94, 638.86, 652.78, 666.70, 680.62, 694.54, 708.46, 722.38, 736.30, 750.22)
P7 = [  # Schedule 4 (business) and Schedule 5 (investment rebate)
    text("name", 165.14, 108.86, SB, 11.04, maxw=300),
    digs("tin", TIN_P7, 123.86, SB, 11.04),
    text("s4.name", 172.0, 150.62, S, 11.04, maxw=390),
    text("s4.nature", 371.0, 165.14, S, 11.04, maxw=190),
    text("s4.address", 78.0, 179.66, S, 11.04, maxw=480),
] + [
    amt(f"s4.r{i}", 545.70, base, font, 11.04) for i, (base, font) in enumerate(S4_ROWS, start=1)
] + [
    text("name", 165.14, 521.47, SB, 11.04, maxw=300),
    digs("tin", TIN_P7B, 536.47, SB, 11.04),
] + [
    amt(f"s5.r{i}", 545.70, base, S, 11.04, zero="dash" if i in (2, 11, 12) else "blank")
    for i, base in enumerate(S5_BASES, start=1)
]

# ---------------------------------------------------------------- page 8
LB_BASES = (217.10, 236.42, 255.74, 275.09, 294.41, 313.73, 333.05, 357.29, 388.13)
P8 = [  # IT-10BB lifestyle expenses
    text("name", 165.14, 137.90, SB, 11.04, maxw=300),
    digs("tin", TIN_P7, 152.90, SB, 11.04),
] + [
    amt(f"lb.r{i}", 462.07, base, S, 9.96) for i, base in enumerate(LB_BASES, start=1)
] + [
    text(f"lb.c{i}", 524.17, base + 0.36, S, 11.04, align="c", maxw=106)
    for i, base in enumerate(LB_BASES, start=1)
] + [
    amt("lb.total", 462.07, 411.41, S, 9.96),
    amt("lb.total2", 574.54, 411.77, S, 11.04),
    text("name", 480.43, 593.23, S, 11.04, align="c", maxw=150),
    text("date", 480.75, 622.15, C, 11.04, align="c", maxw=100),
]
assert len(LIFESTYLE_ROWS) == len(LB_BASES)

# ---------------------------------------------------------------- page 9
P9 = [  # IT-10B page 1: sources, net wealth, liabilities
    text("iy_end_dmy", 252.65, 113.78, SB, 10.08, maxw=80),
    text("name", 159.02, 266.06, SB, 9.24, maxw=300),
    digs("tin", TIN_P9, 280.37, SB, 9.24),
    amt("w.1a", 413.58, 314.57, S, 9.24),
    amt("w.1b", 413.61, 330.53, S, 9.24),
    amt("w.1c", 413.56, 346.49, S, 9.24),
    text("w.gift_label", 194.93, 347.09, SB, 9.24, maxw=128),
    amt("w.src", 476.36, 362.57, S, 9.24),
    amt("w.2", 476.36, 378.53, S, 9.24, zero="blank"),
    amt("w.3", 476.36, 394.49, S, 9.24),
    amt("w.4a", 413.58, 410.33, S, 9.24),
    amt("w.4b", 413.67, 426.29, S, 9.24, color=(1, 0, 0)),
    amt("w.exp", 476.26, 442.37, S, 9.24),
    amt("w.5", 476.36, 458.47, SB, 9.24),
    amt("w.6a", 376.47, 506.11, S, 9.24),
    amt("w.6b", 376.47, 522.07, S, 9.24),
    amt("w.6c", 376.47, 538.03, S, 9.24),
    amt("w.liab", 476.36, 554.11, S, 9.24, dash=474.15),
    amt("w.7", 476.36, 582.43, SB, 9.24),
]

# ---------------------------------------------------------------- page 10
P10 = [  # IT-10B page 2: particulars of assets
    text("name", 123.74, 66.60, SB, 9.24, maxw=160),
    text("tin", 319.27, 66.12, SB, 9.24, maxw=80),
    text("iy_end_mdy", 405.31, 66.60, SB, 10.08, maxw=80),
    amt("a.agg", 378.19, 107.42, S, 9.24, dash=375.87),
    amt("a.bliab", 378.19, 123.26, S, 9.24, dash=375.87),
    amt("a.bcap", 476.26, 137.30, S, 9.24, dash=465.30),
    amt("a.dir", 476.26, 151.46, S, 9.24, dash=465.30),
    amt("a.bcap_other", 476.26, 180.50, S, 9.24, dash=465.30),
    amt("a.d_total", 474.40, 222.38, S, 9.24),
] + [
    text(f"a.d{i}_desc", 70.94, base, SB, 8.40, maxw=274)
    for i, base in zip(range(1, 5), (235.58, 248.42, 261.26, 274.13))
] + [
    amt(f"a.d{i}_val", 413.57, base, S, 9.24, zero="blank", maskw=50)
    for i, base in zip(range(1, 5), (235.22, 248.06, 260.90, 273.77))
] + [
    amt("a.e_total", 476.26, 313.49, S, 9.24, zero="blank"),
    text("a.e_desc", 272.0, 313.49, SB, 8.40, maxw=108),
    amt("a.f1", 395.98, 346.01, S, 9.24, dash=393.87),
    amt("a.f2", 395.98, 363.65, S, 9.24, dash=393.87),
    amt("a.f3", 395.98, 381.29, S, 9.24, dash=393.87),
    amt("a.f4", 395.98, 396.53, S, 9.24, dash=393.87),
    amt("a.f5", 395.98, 427.01, S, 9.24, zero="blank"),
    amt("a.f6", 395.98, 439.85, S, 9.24, dash=393.87),
    amt("a.f7", 395.98, 452.71, S, 9.24, dash=393.87),
    amt("a.f_total", 476.26, 465.55, S, 9.24),
    amt("a.g", 476.26, 505.27, S, 9.24, zero="blank"),
    text("a.g_desc", 300.0, 521.23, S, 9.24, maxw=176),
    amt("a.h", 476.26, 548.83, S, 9.24, dash=474.15),
    dict(kind="ornaments", key="a.h_qty", x=195.05, base=549.79, size=10.08, maxw=94),
    text("a.h_note", 291.77, 549.19, S, 9.24, maxw=88),
    amt("a.i", 476.26, 567.31, S, 9.24, dash=474.15),
    text("a.i_note", 291.77, 567.67, S, 9.24, maxw=88),
    amt("a.j", 476.26, 584.83, S, 9.24, dash=474.15),
    amt("a.k", 476.26, 603.19, S, 9.24, dash=474.15),
    amt("a.total", 476.36, 638.62, SB, 9.24),
    text("name", 403.62, 738.58, SB, 9.24, align="c", maxw=160),
    text("date", 388.63, 762.70, S, 9.24, maxw=100),
]

# ---------------------------------------------------------------- page 11
SLAB_INC = (196.70, 209.78, 222.86, 235.94, 249.02, 262.10)
SLAB_TAX = (196.58, 209.66, 222.74, 235.82, 248.90, 261.98)
J_BASES = (622.99, 636.10, 649.18, 662.26, 675.34, 688.42, 701.50)
P11 = [  # Tax computation sheet
    text("name_line", 309.55, 61.92, AB, 10.8, align="c", maxw=300),
    text("tin", 307.49, 75.00, AB, 10.8, maxw=120),
    text("iy_end_dmy", 341.59, 88.08, AB, 10.8, maxw=80),
    amt("tc.A", 516.13, 124.10, C, 9.96),
    amt("tc.sp", 516.17, 137.18, C, 9.96, dash=506.07),
    amt("tc.An", 516.13, 151.34, C, 9.96),
]
for _i in range(6):
    P11 += [amt(f"tc.s{_i}.inc", 406.75, SLAB_INC[_i], S, 9.96, dash=396.87),
            text(f"tc.s{_i}.rate", 413.83, SLAB_INC[_i], S, 9.96, maxw=24),
            amt(f"tc.s{_i}.tax", 515.64, SLAB_TAX[_i], S, 9.96, dash=505.74)]
P11 += [
    amt("tc.sinc", 406.76, 275.21, S, 9.96),
    amt("tc.B", 514.77, 275.21, S, 9.96),
    amt("tc.ci", 406.50, 315.41, S, 10.8),
    amt("tc.cii", 406.63, 329.21, S, 10.8, dash=395.83),
    amt("tc.ciii", 406.50, 342.29, S, 10.8),
    amt("tc.C", 515.70, 355.01, S, 9.96, dash=505.74),
    amt("tc.D", 516.01, 374.45, CB, 9.96),
    amt("tc.ei", 407.14, 413.69, CB, 9.96, dash=397.08),
    amt("tc.eii", 407.18, 426.77, CB, 9.96, dash=397.08),
    amt("tc.eiii", 407.18, 439.85, CB, 9.96, dash=397.08),
    amt("tc.E", 515.64, 453.07, S, 9.96, dash=505.74),
    amt("tc.F", 516.01, 479.11, CB, 9.96),
    amt("tc.gs", 407.18, 518.35, CB, 9.96, dash=397.08),
    amt("tc.gd", 407.18, 531.43, CB, 9.96, zero="blank"),
    amt("tc.G", 516.05, 531.43, CB, 9.96, dash=505.95),
    amt("tc.H", 516.05, 557.59, CB, 9.96, dash=505.95),
    amt("tc.I", 516.01, 583.75, CB, 9.96),
] + [
    amt(f"tc.j{i}", 407.16, base, A, 9.0, dash=397.15) for i, base in enumerate(J_BASES, start=1)
] + [
    amt("tc.jsub1", 516.17, 675.34, C, 9.96, dash=506.07),
    amt("tc.jsub2", 516.17, 701.50, C, 9.96, dash=506.07),
    amt("tc.K", 516.01, 717.46, CB, 9.96),
    amt("tc.paid", 516.17, 757.54, C, 9.96, dash=506.07),
    text("tc.challan", 203.5, 770.62, AB, 8.16, maxw=200),
    amt("tc.net", 516.12, 782.86, C, 9.96),
]

# ---------------------------------------------------------------- page 12
TF_BASES = (137.18, 150.50, 163.94, 177.62, 191.30, 204.98, 219.14, 232.82, 246.50, 260.18, 273.89,
            287.57, 301.25, 314.93, 328.61, 341.93, 355.37, 369.05, 382.73, 396.41, 409.61, 423.29)
P12 = [  # Tax-free (exempted) income sheet
    text("name_line", 300.55, 61.80, AB, 10.8, align="c", maxw=300),
    text("tin", 248.21, 75.60, AB, 10.8, maxw=120),
    text("iy_end_dmy", 282.29, 88.68, AB, 10.8, maxw=80),
] + [
    amt(f"tf.r{i:02d}", 552.00, base + 0.48, S, 9.96, zero="blank")
    for i, base in enumerate(TF_BASES, start=1)
] + [
    amt("tf.total", 552.00, 436.49, SB, 9.96),
]

PAGES = [P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12]


def masks(field):
    """Regions (x0, x1, base_lo, base_hi) where the sample shows this field's data."""
    k = field["kind"]
    b = field["base"] if "base" in field else None
    if k == "amount":
        return [(field["right"] - field["maskw"], field["right"] + 14, b - 1.5, b + 1.5)]
    if k == "digits":
        return [(c - 4, c + 4, b - 1.5, b + 1.5) for c in field["centers"]]
    if k == "check":
        x0, top, x1, bot = field["box"]
        return [(x0, x1 + 1, top, bot + 2)]
    if k == "relation":
        return [(field["x"] - 1, field["x"] + 76, b - 1.5, b + 1.5)]
    if k == "ornaments":
        return [(field["x"] - 2, field["x"] + field["maxw"] - 25, b - 1.5, b + 1.5)]
    x, w = field["x"], field["maxw"]
    x0, x1 = {"l": (x - 2, x + w), "c": (x - w / 2, x + w / 2), "r": (x - w, x + 2)}[field["align"]]
    return [(x0, x1, b - 1.5, b + 1.5 + (field["lines"] - 1) * field["lead"])]
