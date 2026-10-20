"""Find and register the fonts the sample return uses.

The sample was printed from Excel with Times New Roman, Calibri, Arial, Tahoma
(for the Taka sign) and MS Gothic (for the tick). On Windows and macOS the real
fonts are used; on Linux the metric-compatible Liberation Serif/Sans and Carlito
give identical text widths. If nothing is found, ReportLab's built-in Times and
Helvetica are used, and the tick is drawn as lines.

Set ERETURN_FONT_DIR to a folder of .ttf files to force a specific set.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

CANDIDATES = {
    "serif": ["times.ttf", "Times New Roman.ttf", "LiberationSerif-Regular.ttf", "Tinos-Regular.ttf"],
    "serif-bold": ["timesbd.ttf", "Times New Roman Bold.ttf", "LiberationSerif-Bold.ttf", "Tinos-Bold.ttf"],
    "sans": ["arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf", "Arimo-Regular.ttf"],
    "sans-bold": ["arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf", "Arimo-Bold.ttf"],
    "calibri": ["calibri.ttf", "Calibri.ttf", "Carlito-Regular.ttf"],
    "calibri-bold": ["calibrib.ttf", "Calibri Bold.ttf", "Carlito-Bold.ttf"],
    "taka": ["tahoma.ttf", "Tahoma.ttf", "FreeSerif.ttf", "FreeSans.ttf", "NotoSansBengali-Regular.ttf",
             "vrinda.ttf", "Nirmala.ttf"],
    "symbol": ["seguisym.ttf", "DejaVuSans.ttf", "Segoe UI Symbol.ttf"],
}
FALLBACK = {
    "serif": "Times-Roman", "serif-bold": "Times-Bold", "sans": "Helvetica", "sans-bold": "Helvetica-Bold",
    "calibri": "Helvetica", "calibri-bold": "Helvetica-Bold", "taka": None, "symbol": None,
}
# Glyph each optional role must contain.
NEEDS = {"taka": "\u09f3", "symbol": "\u2714"}


def _font_dirs() -> list[Path]:
    dirs = []
    if os.environ.get("ERETURN_FONT_DIR"):
        dirs.append(Path(os.environ["ERETURN_FONT_DIR"]))
    dirs.append(Path(__file__).parent / "fonts")
    if sys.platform.startswith("win"):
        dirs.append(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts")
        dirs.append(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts")
    elif sys.platform == "darwin":
        dirs += [Path.home() / "Library/Fonts", Path("/Library/Fonts"),
                 Path("/System/Library/Fonts/Supplemental"), Path("/System/Library/Fonts")]
    dirs += [Path.home() / ".fonts", Path.home() / ".local/share/fonts", Path("/usr/local/share/fonts"),
             Path("/usr/share/fonts")]
    return [d for d in dirs if d.is_dir()]


def _index() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for d in _font_dirs():
        for p in d.rglob("*.tt[fF]"):
            found.setdefault(p.name.lower(), p)
    return found


class Fonts:
    """Maps the template's font roles to registered ReportLab font names."""

    def __init__(self):
        self.names: dict[str, str | None] = {}
        self.files: dict[str, str] = {}
        index = _index()
        for role, files in CANDIDATES.items():
            self.names[role] = FALLBACK[role]
            for fname in files:
                path = index.get(fname.lower())
                if not path:
                    continue
                try:
                    font = TTFont(f"ER-{role}", str(path))
                except Exception:
                    continue
                if role in NEEDS and ord(NEEDS[role]) not in font.face.charToGlyph:
                    continue
                pdfmetrics.registerFont(font)
                self.names[role] = f"ER-{role}"
                self.files[role] = str(path)
                break

    def get(self, role: str) -> str:
        return self.names.get(role) or FALLBACK.get(role) or "Helvetica"

    def has(self, role: str) -> bool:
        return self.names.get(role) is not None and role in self.files

    def report(self) -> str:
        return ", ".join(f"{r}={Path(self.files[r]).name if r in self.files else self.names[r] or 'vector'}"
                         for r in CANDIDATES)
