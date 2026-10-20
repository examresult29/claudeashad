=== BD e-Return ===
Contributors: examresult29
Tags: tax, income tax, bangladesh, e-return, nbr
Requires at least: 5.8
Requires PHP: 7.4
Stable tag: 1.0.0
License: GPLv3 or later
License URI: https://www.gnu.org/licenses/gpl-3.0.html

Bangladesh individual income tax return calculator. Works out the tax as you type and prints the 12-page return as a PDF.

== Description ==

Fill in a taxpayer's figures and get the complete return, laid out like the familiar Excel template:

* IT-11 Chha (2023) acknowledgement receipt
* IT-11GA 2023 return of income, pages 1-3
* Schedule 1 (salary: Government pay scale and private), Schedule 2 (house property), Schedule 3 (agriculture), Schedule 4 (business), Schedule 5 (investment rebate)
* IT-10BB (2023) lifestyle expenses
* IT-10B (2023) assets, liabilities and expenses
* Tax computation sheet and tax-free income sheet

The tax computation updates as you type: tax-free limit by category, slab tax, investment rebate, minimum tax, net wealth surcharge, tax already paid and the balance to pay with the return. Warnings point out a wealth statement that does not balance, a deficit, or minimum tax applying.

Privacy: the calculation and the PDF are made in the browser. Nothing is sent to or stored on your server. A draft is kept in the visitor's own browser until they press "Clear form"; "Save data" downloads it as a file that "Open saved data" reloads later.

Tax rules: choose "AY 2026-27 (Finance Act 2026, as reported)", "Sample template (older 5% slab)" or "Finance Ordinance 2025". The AY 2026-27 figures come from news reports of the Finance Act 2026, not the official gazette, so check them before filing. The rule files are in assets/data/rules/ and can be edited.

== Installation ==

1. In WordPress go to Plugins > Add New > Upload Plugin, choose bd-e-return.zip and click Install Now, then Activate.
2. Open the new "e-Return" item in the admin menu, or add the shortcode [bd_e_return] to any page.

Shortcode options:

* [bd_e_return login="yes"] shows the form only to logged-in users.
* [bd_e_return profile="sample-template"] preselects a tax rules profile (ay2026-27, sample-template or fo2025).

== Frequently Asked Questions ==

= Where is the taxpayer's data stored? =

Only in the visitor's browser (local storage) as a draft. Use "Save data" to keep a copy as a file.

= Can I use Bangla text? =

Enter names and addresses in English letters, as on the printed form. Letters the standard PDF fonts cannot show are replaced with "?".

= How do I change the tax slabs? =

Edit the JSON files in assets/data/rules/. Each profile needs a tax-free threshold per category and five slabs after it (the last one open-ended).

== Changelog ==

= 1.0.0 =
* First release.
