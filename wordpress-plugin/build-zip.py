"""Build dist/bd-e-return.zip, the file to upload in WordPress (Plugins > Add New > Upload Plugin).

The page layout, field positions, rules and examples are first copied from the Python engine
(bd-e-return/skills/e-return), so the plugin always prints what the engine prints.
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "bd-e-return"
OUT = HERE / "dist" / "bd-e-return.zip"
SKIP = {"standalone.html"}  # local test page; on a live site it would bypass the login="yes" option
ENGINE = HERE.parent / "bd-e-return" / "skills" / "e-return"

sys.path.insert(0, str(ENGINE))
from ereturn.fields import PAGES  # noqa: E402

data = SRC / "assets" / "data"
shutil.copyfile(ENGINE / "ereturn" / "template.json", data / "template.json")
(data / "fields.json").write_text(json.dumps(PAGES, separators=(",", ":")), encoding="utf-8")
for rules in (ENGINE / "ereturn" / "rules").glob("*.json"):
    shutil.copyfile(rules, data / "rules" / rules.name)
for example in ("sample-reproduction.json", "private-employee.json"):
    shutil.copyfile(ENGINE / "examples" / example, data / "examples" / example)
shutil.copyfile(ENGINE / "ereturn" / "assets" / "emblem.png", SRC / "assets" / "img" / "emblem.png")

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(SRC.rglob("*")):
        if p.is_file() and p.name not in SKIP and "__pycache__" not in p.parts:
            z.write(p, Path("bd-e-return") / p.relative_to(SRC))
print(f"{OUT} ({OUT.stat().st_size // 1024} KB)")
