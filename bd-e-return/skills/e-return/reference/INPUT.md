# Input file reference

The engine reads one JSON object. Every amount is in taka (numbers or strings such
as `"1,23,456"`). Anything left out is zero or blank. `*` marks the only required
fields. Line numbers refer to the printed pages:

- **Ret.** = Return of income IT-11GA 2023 (lines 1-26)
- **S1-S5** = Schedules 1-5, **BB** = IT-10BB, **B** = IT-10B
- **TC** = tax computation sheet, **TF** = tax-free income sheet

## Top level

| key | meaning |
|---|---|
| `rules_profile` | `ay2026-27` (default), `sample-template` or `fo2025`. See `ereturn/rules/*.json`. |
| `assessment_year` | `"2026-2027"` (also accepts `"2026-27"`). The income year ends 30 June of the first year. |

## `taxpayer`

| key | meaning |
|---|---|
| `name`* | Name of the assessee (all pages). |
| `tin`* | 12-digit TIN (printed in the boxes). |
| `nid` / `passport` | NID, or passport number if no NID. |
| `circle`, `tax_zone` | Tax circle and zone. |
| `resident` | `true` (default) ticks Resident, `false` ticks Non-resident. |
| `gender` | `"female"` gives the women's threshold; `"third_gender"` the third-gender threshold. |
| `category` | Extra categories (list): `senior`, `disabled`, `third_gender`, `war_wounded_freedom_fighter`, `july_joddha`. The highest threshold applies. Age 65+ is detected from `dob`. |
| `parent_of_disabled` | `true` adds Tk 50,000 to the threshold. |
| `dob` | Date of birth, `YYYY-MM-DD` or `DD/MM/YYYY`. |
| `spouse_name`, `spouse_tin` | Spouse details. |
| `father_or_husband`, `relation` | Name for the verification; `relation` is `"father"` (default) or `"husband"` (that word is printed bold). |
| `address`, `telephone`, `mobile`, `email` | Contact details. |
| `employer` | Employing institution (Ret. line 11). |
| `organization`, `bin`, `partners` | Ret. line 12-13 (business/firm). |
| `first_return` | `true` on a first return: "(First Return)" label on B 1(c), Tk 1,000 minimum tax in profiles that have it, and the wealth statement balances through "Receipt of gift and others". |
| `location` | Only for a profile whose minimum tax depends on location. |

## `form`

| key | meaning |
|---|---|
| `place`, `date` | Place and date of signing. |
| `special_benefit_boxes` | `"auto"` (default) ticks the boxes for the categories used; or a list such as `["female"]`; `[]` leaves them blank (as the sample did). |
| `documents` | Up to 7 lines for "List of documents furnished". Default: Tax Calculation, Tax Free Income/ Exempted, Related Supporting Documents. |

## `salary`

`govt` (S1 part a, Government pay scale): `basic_pay`, `arrear_pay`,
`special_allowance`, `house_rent_allowance`, `medical_allowance`,
`conveyance_allowance`, `festival_allowance`, `support_staff_allowance`,
`leave_allowance`, `honorarium`, `overtime_allowance`, `baishakhi_allowance`,
`pf_interest`, `lamp_grant`, `gratuity`, `others`. Items listed in the profile's
`govt_salary_taxable_items` are taxable, the rest exempt.

`private` (S1 part b): `basic_pay`, `allowances`, `advance_salary`,
`gratuity_pension`, `perquisites`, `in_lieu_of_salary`, `employee_share_scheme`,
`accommodation`, `car_benefit`, `other_benefits`, `employer_pf_contribution`,
`others`. Exempt = lower of one third or the profile's cap.

Overrides: `govt_taxable_items` (list), `private_exemption` (amount).

Ret. line 1 = S1(a) taxable total + S1(b) line 15.

## `house_property` (S2, Ret. line 2)

A list; several properties are added together on one schedule.

| key | meaning |
|---|---|
| `description` | Location and description (left column of S2). |
| `annual_value` | Rent received or annual value, whichever is higher (line 1). |
| `advance_rent`, `other_benefits` | Lines 2 and 3. |
| `adjusted_advance_rent`, `vacancy_allowance` | Lines 4 and 5 (deducted). |
| `type` | `residential` (25% repair allowance) or `commercial` (30%). |
| `repair_rate` | Override the allowance, for example `0.25`. |
| `municipal_tax`, `land_revenue`, `loan_interest`, `insurance_premium`, `other_deductions` | Deductions 7(b)-(f). |
| `ownership_share` | For example `0.5`; line 10 then carries the share. |

## `agriculture` (S3, Ret. line 3)

`nature`, `turnover`, `gross_profit`, `expenses`. Net profit = gross profit - expenses.

## `business` (S4, Ret. line 4)

`name`, `nature`, `address`, `turnover`, `gross_profit`, `expenses`, `bad_debt`
(net profit = gross profit - expenses - bad debt), and `balance_sheet`:
`cash_bank`, `inventory`, `fixed_assets`, `other_assets`, `opening_capital`,
`drawings`, `liabilities`. Closing capital (opening + profit - drawings) becomes
the business capital on B 8(a).

## `other_income`

| key | Ret. line |
|---|---|
| `capital_gains` | 5 |
| `financial_assets` | 6 (bank interest, dividend, securities) |
| `sanchayapatra_interest` | 6, and deducted on TC "Less: Sanchayapatra": taxed finally through its TDS (TC H) |
| `other_sources` | 7 |
| `firm_share` | 8 |
| `minor_spouse` | 9 |
| `foreign` | 10 |

## `exempt_income` (TF, Ret. line 26, B 1(b))

Row 01 is filled automatically with the salary exemption. Other rows:
`salary_other` (added to row 01), `govt_pf`, `taxed_distribution`,
`pf_1925_income`, `voluntary_retirement`, `pensioners_savings_certificate`,
`firm_capital_share`, `huf_share`, `foreign_remittance`, `wage_earners_fund`,
`hill_tracts`, `agricultural`, `software_it`, `handicrafts_export`, `sme`,
`zero_coupon`, `govt_pension`, `welfare_allowance`, `govt_award`,
`briddhashram`, `seagoing_ship`, `other`.

## `investments` (S5 rows 1-10, rebate)

`life_insurance`, `dps`, `govt_securities`, `listed_securities`, `pf_1925`,
`rpf`, `pension_fund`, `benevolent_group_insurance`, `zakat`, `others`. Enter
the allowable amounts (for example DPS up to its limit).

## `tax`

| key | meaning |
|---|---|
| `min_tax_163_2kha`, `min_tax_163_5ka` | Other minimum-tax amounts (TC E ii, iii). |
| `minimum_tax` | Override TC E i. |
| `surcharge_trigger` | `true` if the taxpayer owns more than one car or a house over 8,000 sft in a city corporation (10% surcharge even below Tk 4 crore). |
| `net_wealth_surcharge` | Override the computed surcharge. |
| `environmental_surcharge` | Car environmental surcharge (Ret. 17b). |
| `delay_interest` | Delay interest or penalty (Ret. 18). |
| `final_tax` | Override TC H (final tax on savings-certificate interest). |
| `rebate_allowed` | `false` to give no rebate. |

## `payments`

| key | meaning |
|---|---|
| `tds_salary` | TC J "Remuneration" |
| `ait_sanchayapatra`, `ait_wppf`, `ait_car`, `ait_bank_interest` | Other tax at source. All five add up to Ret. line 20. |
| `advance_tax` | Ret. line 21 |
| `refund_adjustment`, `refund_assessment_years` | Ret. line 22 |
| `paid_with_return` | Amount paid by A-challan with the return. Leave it out and the balance due is assumed paid (Ret. line 23), as in the sample. |
| `challan_number` | Printed on the TC sheet. |

## `lifestyle` (BB)

`food_clothing`, `housing`, `transport`, `utility`, `education`, `travel`,
`festival`, `loan_interest`; `tax_paid` defaults to Ret. line 24 (all tax paid
and adjusted for this return). `comments` holds a note per row, for example
`{"housing": "Family House"}`.

## `wealth` (B)

| key | meaning |
|---|---|
| `previous_net_wealth` | Net wealth on last year's IT-10B (line 2). Leave out on a first return. |
| `balancing_item` | Which figure absorbs the difference so the statement balances: `gift` (default on a first return: B 1(c) "Receipt of gift and others" = assets - liabilities + expenses - income - previous wealth), `cash` (default otherwise: cash and bank = everything else), or `none` (you give everything; a warning shows any difference). |
| `gift_and_other_receipts`, `gift_label` | B 1(c) when not balancing on it; label defaults to "(First Return)" on a first return. |
| `other_outflows` | B 4(b) gifts given, losses, expenses not in IT-10BB. |
| `liabilities` | `institutional`, `non_institutional`, `other`. |
| `assets` | see below |

`assets`: `business_capital_aggregate` and `business_liabilities` (only when
there is no S4 balance sheet), `director_shareholdings`,
`non_agricultural_property` and `agricultural_property` (lists of
`{"description", "value"}`; 4 lines fit for non-agricultural property),
`debenture_bond`, `sanchayapatra_dps`, `life_insurance`, `loan_given`, `fdr`,
`provident_fund`, `other_investment`, `motor_car`, `motor_car_details`,
`ornaments` (value), `ornaments_quantity` (e.g. `"25 Bhori"`), `ornaments_type`
(default `"(Gold)"`), `ornaments_note`, `furniture_electronics`,
`furniture_note`, `other_assets`, `cash_bank`.
