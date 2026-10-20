# bd-e-return: Bangladesh income tax return plugin for Claude Code

Give Claude a taxpayer's information; it calculates the tax and prints the full
return as a 12-page PDF, laid out like the sample Excel template (same forms,
positions, fonts and number formats):

1. IT-11 Chha (2023) acknowledgement receipt
2. IT-11GA 2023 return, pages 1-3
3. Schedule 1 (salary), Schedules 2-3 (house property, agriculture), Schedules 4-5 (business, investment rebate)
4. IT-10BB (2023) lifestyle expenses
5. IT-10B (2023) assets, liabilities and expenses, pages 1-2
6. Tax calculation sheet
7. Tax-free (exempted) income sheet

How every figure is worked out, using the sample return, is in
[docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md).

## Use it

**In this repository** (Claude Code on the web or locally): the skill is already
available. Ask, for example:

> Make the e-return for AY 2026-27: Rahima Khatun, TIN 123456789012, Government
> school teacher, basic pay 3,60,000, festival allowance 60,000, Baishakhi 6,000,
> house rent from the family house 1,80,000 a year, DPS 60,000, ...

Claude asks for anything missing, runs the engine and gives you the PDF.

**In another project:** add this repository as a plugin marketplace and install
the plugin:

```
/plugin marketplace add examresult29/claudeashad
/plugin install bd-e-return@claudeashad
```

Then use `/bd-e-return:tax-return <details>` or just describe the return.

**From the command line** (Python 3.9+ and `pip install reportlab`):

```
cd bd-e-return/skills/e-return
python3 -m ereturn examples/sample-reproduction.json -o sample.pdf
```

The input format is documented in
[skills/e-return/reference/INPUT.md](skills/e-return/reference/INPUT.md).

## Tax rules

The slab table is chosen with `rules_profile` (files in
`skills/e-return/ereturn/rules/`):

- `ay2026-27` (default): AY 2026-27 as reported for the Finance Act 2026.
- `sample-template`: the rules the sample template used (older 5% band); reproduces the sample exactly.
- `fo2025`: Finance Ordinance 2025 as first announced.

The AY 2026-27 figures come from news reports, not the official gazette. Check
them before filing and edit the JSON file if they differ.

## Privacy

Returns contain NID, TIN, income and assets. This repository is public: keep
input files and PDFs in `returns/`, which is git-ignored. The committed examples
use placeholder identities.

## Fonts

The template uses Times New Roman, Calibri, Arial and Tahoma. They are used when
installed (Windows, macOS); otherwise the metric-compatible Liberation and
Carlito fonts give identical spacing. Set `ERETURN_FONT_DIR` to use a particular
folder of `.ttf` files.

## Development

- `python3 skills/e-return/tests/test_engine.py` checks every figure of the sample and several other cases.
- `skills/e-return/tools/build_template.py` rebuilds the blank form (`ereturn/template.json`) from a filled sample PDF if the layout changes.
- `skills/e-return/ereturn/fields.py` lists where each value is printed.
