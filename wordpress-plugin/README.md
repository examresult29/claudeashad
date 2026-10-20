# BD e-Return for WordPress

A WordPress plugin with the same calculator and 12-page return PDF as the Python
engine in `bd-e-return/`, running entirely in the visitor's browser: nothing is
sent to or stored on the server.

**Install:** in WordPress go to Plugins > Add New > Upload Plugin and upload
`dist/bd-e-return.zip`, then activate it. Use the new "e-Return" admin page, or put
the shortcode on any page:

```
[bd_e_return]                          the form, for everyone
[bd_e_return login="yes"]              only for logged-in users
[bd_e_return profile="sample-template"]  preselect a rules profile (ay2026-27, sample-template, fo2025)
```

The admin page is shown to users who can edit posts; change that with the
`bder_capability` filter.

**Layout of the plugin:**

- `bd-e-return.php`: shortcode, admin page, script loading.
- `assets/js/calc.js`: the tax engine, a line-by-line port of `ereturn/calc.py` (same figures on every test case).
- `assets/js/render.js`: draws the 12 pages with pdf-lib, a port of `ereturn/render.py`.
- `assets/js/app.js`, `assets/css/app.css`: the form, live tax panel and PDF buttons.
- `assets/data/`: page layout, field positions, rules and examples, copied from the Python engine.
- `assets/vendor/`: pdf-lib and fontkit (MIT); `assets/fonts/`: Carlito (OFL) and a Taka-sign subset of FreeSerif (GPL with font exception).

**Rebuild the zip** after changing the engine's data or the plugin:

```
python3 wordpress-plugin/build-zip.py
```

It copies the layout, field positions, rules and examples from `bd-e-return/skills/e-return`
first, so the plugin prints exactly what the engine prints. `bd-e-return/standalone.html`
runs the app without WordPress for testing (serve the folder over HTTP); it is left
out of the zip.
