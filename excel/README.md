# BD e-Return calculator (Excel)

`BD-e-Return-Calculator.xlsx` works out a Bangladesh individual income tax return
with live formulas and prints it as the same 12 pages as the sample return:
acknowledgement (IT-11 Chha), return pages 1-3 (IT-11GA 2023), Schedules 1-5,
IT-10BB, IT-10B pages 1-2, the tax calculation sheet and the tax-free income sheet.

It opens filled in with an anonymised copy of the sample return, so you can see
what goes where. Replace those figures with your taxpayer's.

## Sheets

| Sheet | What it is |
|---|---|
| **Input** | Everything you type: peach cells with blue text. Results and checks are at the top. |
| **Rules** | Tax-free limits, slabs, minimum tax, rebate and surcharge for each rules profile. |
| **Calc** | Every figure of the return as a formula, with its name (`v_...`). Protected. |
| **P01-P12** | The 12 printed pages, laid out like the sample. Protected. |

## Fill it in

1. On **Input**, choose the **Tax rules** profile:
   - `ay2026-27`: AY 2026-27 as reported for the Finance Act 2026.
   - `sample-template`: the older slab table the sample used (5% band). Use it to reproduce the sample.
   - `fo2025`: Finance Ordinance 2025 as first announced.
2. Type the taxpayer's details and figures in the peach cells. Leave a cell empty for zero.
   Cells with a list (Yes/No, Residential/Commercial, ...) have a drop-down.
3. Read **Results** and **Checks** at the top of Input. Checks say, for example, that
   the wealth statement does not balance or that minimum tax applies.

Room on the form: 3 house properties, 4 non-agricultural and 2 agricultural property
lines, 7 documents. The wealth statement balances itself: without last year's net
wealth (a first return) through "receipt of gift and others", otherwise through cash
and bank. You can pick the balancing item on Input instead.

## Print or save as PDF

1. Click the tab **P01 Acknowledgement**, hold **Shift**, click **P12 Tax free income**.
2. Press **Ctrl+P** (Mac: Cmd+P), keep A4 and "Print Active Sheets". For a PDF, use
   File > Save As, choose PDF, and under Options pick "Active sheet(s)".

Each tab prints on exactly one A4 page with the sample's margins; do not change the
scaling. Pages P09-P12 are set to 84% and 90%, as the sample printed them.

## Change a tax rate

Edit the profile's column on **Rules**; every formula picks the change up. The
AY 2026-27 figures come from news reports, not the official gazette: check them
before filing.

## Fonts

The pages use Times New Roman, Calibri, Arial, Tahoma (for the Taka sign) and MS Gothic
(for the tick), as the sample does. Windows has all of them. LibreOffice and Excel for
Mac substitute look-alike fonts, so a few labels can move by a point or two.

## How it was checked

- The formulas were compared with the Python engine in `bd-e-return/` on 11 test
  returns (338 figures each): no differences, and no formula errors.
- The print pages were exported to PDF with LibreOffice and compared word by word with
  the sample's layout. Words land within about 2 points of the sample (LibreOffice
  pads cells slightly less than Excel), and no number overflows its cell.

## Rebuild

The workbook is generated; edit the scripts, not the file:

```
pip install openpyxl reportlab
python3 excel/build_workbook.py [output.xlsx] [example.json]
```

`layout.py` turns each measured page of the sample into an Excel grid: every border,
shaded box and text position becomes a column or row edge, sized on Excel's 96-dpi
pixel grid. `build_workbook.py` writes the Input, Rules and Calc sheets and the 12
pages. The example input format is in `bd-e-return/skills/e-return/reference/INPUT.md`.

This calculator helps prepare a return; it is not tax advice. Check the figures, and
the current law, before you file.
