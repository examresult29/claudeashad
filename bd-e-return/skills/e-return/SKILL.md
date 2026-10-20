---
name: e-return
description: Prepare a Bangladesh individual income tax return (e-Return, IT-11GA 2023 with Schedules 1-5, IT-10BB lifestyle statement, IT-10B assets statement, tax computation sheet and tax-free income sheet) as a 12-page PDF laid out exactly like the user's Excel template. Use when the user gives a taxpayer's information (salary, house rent, business, investments, tax deducted, expenses, assets) and wants the tax calculated or the return PDF made, or asks how a figure on such a return is worked out.
---

# Bangladesh e-Return (IT-11GA 2023) generator

This folder holds a calculation engine (`ereturn/`) and a renderer that prints the
same 12 pages, in the same positions and fonts, as the sample return it was built
from. Your job is to turn what the user tells you into an input JSON, run the
engine, check its warnings, and hand over the PDF.

Paths below are relative to this skill's base directory (the folder containing
this file). Run commands from there.

## 1. Collect the information

Ask only for what is missing; everything not given defaults to zero/blank.
Read `reference/INPUT.md` for every field and the form line it feeds.

Needed for every return:
- Identity: name, 12-digit TIN, NID (or passport), circle, tax zone, date of birth,
  father's or husband's name, address, gender, resident or not, first return or not.
- Income for the income year (July-June): salary (Government pay scale items, or
  private basic/allowances/perquisites), house rent, agriculture, business, bank
  interest/dividend, savings-certificate (sanchayapatra) interest, other income.
- Tax-rebate investments (DPS, life insurance, provident fund contributions, shares, savings certificates bought).
- Tax already paid: TDS from salary, AIT on savings certificates/bank interest, advance tax, refund adjusted.
- Lifestyle expenses for IT-10BB (food/clothing, housing, transport, utilities, education, travel, festivals, loan interest).
- Assets and liabilities at 30 June for IT-10B, and last year's net wealth
  (blank on a first return).

## 2. Pick the tax rules

`rules_profile` selects the slab table (files in `ereturn/rules/`):

| profile | use it when |
|---|---|
| `ay2026-27` (default) | AY 2026-27 as reported for the Finance Act 2026: Tk 4,00,000 general / 4,50,000 women and 65+ threshold, 10-15-20-25-30% slabs, minimum tax Tk 5,000 (Tk 1,000 first return). |
| `sample-template` | Reproduce the user's sample template exactly (older 5% band, women Tk 4,00,000). |
| `fo2025` | Finance Ordinance 2025 figures (Tk 3,75,000 threshold). |

Tell the user which profile you used. The rule figures come from news reports, not
the gazette; if the user says their figures differ, edit or copy a rules file
rather than hard-coding numbers.

## 3. Build the input and run

1. Write the input JSON outside this plugin folder (for example
   `returns/<name>-<AY>.json` in the user's project). It holds personal data: do
   not commit it to a public repository unless the user asks.
2. Make sure the dependency is installed: `python3 -c "import reportlab"` or
   `pip install reportlab`.
3. Run:
   ```
   python3 -m ereturn <input.json> -o <output.pdf> --summary-json <figures.json>
   ```
   It prints the key figures, the fonts used, and warnings.
4. Act on warnings before delivering:
   - Negative balancing figure (cash or "receipt of gift") or "IT-10B does not
     balance": the assets, liabilities, expenses and income don't reconcile. Ask
     the user which figure is wrong rather than inventing one.
   - "Deficit": the return still shows tax unpaid; confirm how it will be paid.
   - Minimum tax applies, surcharge applies, more than 4 properties: mention them.

## 4. Deliver

Give the user the PDF (send the file if you can) and a short summary: total
income, tax-exempt income, gross tax, rebate, minimum tax, tax payable, amount
already paid, amount to pay with the return, net wealth, and the rules profile.
To explain any figure, use `../../docs/HOW-IT-WORKS.md`, which walks through every
line of the sample return and the formulas behind it.

## Reference

- `reference/INPUT.md`: every input field.
- `examples/sample-reproduction.json`: the sample's figures (placeholder identity); reproduces the sample PDF exactly.
- `examples/private-employee.json`: a fuller case (private salary, rent, savings certificates, investments, TDS, liabilities).
- `tests/test_engine.py`: run `python3 tests/test_engine.py` after changing rules or code.
- `tools/build_template.py`: rebuilds `ereturn/template.json` from a filled sample PDF if the form layout changes.
