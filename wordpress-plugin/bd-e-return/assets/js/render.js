/*!
 * BD e-Return PDF renderer (JavaScript port of ereturn/render.py), built on pdf-lib.
 *
 * render(V, assets) -> Promise<Uint8Array>
 *   V      : figures from BDERCalc.compute()
 *   assets : { PDFLib, fontkit, template, fields, emblem, carlito, carlitoBold, taka }
 *            (the last four are font/image bytes as Uint8Array or ArrayBuffer)
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BDERRender = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function rnd(x) { var r = Math.floor(Math.abs(x) + 0.5 + 1e-9); return x < 0 ? -r : r; }

  function fmtAmount(v) {
    var s = Math.abs(rnd(v)).toLocaleString("en-US");
    return rnd(v) < 0 ? "(" + s + ")" : s;
  }

  async function render(V, A) {
    var L = A.PDFLib;
    var pdf = await L.PDFDocument.create();
    pdf.registerFontkit(A.fontkit);
    var F = {
      "serif": await pdf.embedFont(L.StandardFonts.TimesRoman),
      "serif-bold": await pdf.embedFont(L.StandardFonts.TimesRomanBold),
      "sans": await pdf.embedFont(L.StandardFonts.Helvetica),
      "sans-bold": await pdf.embedFont(L.StandardFonts.HelveticaBold),
      "calibri": await pdf.embedFont(A.carlito, { subset: true }),
      "calibri-bold": await pdf.embedFont(A.carlitoBold, { subset: true }),
      "taka": await pdf.embedFont(A.taka, { subset: true })
    };
    var STANDARD = { "serif": 1, "serif-bold": 1, "sans": 1, "sans-bold": 1 };
    var emblem = await pdf.embedPng(A.emblem);
    var H = A.template.height, W = A.template.width;
    var page;

    function color(c) {
      if (c === null || c === undefined) return L.rgb(0, 0, 0);
      if (typeof c === "number") return L.rgb(c, c, c);
      if (c.length === 1) return L.rgb(c[0], c[0], c[0]);
      if (c.length === 3) return L.rgb(c[0], c[1], c[2]);
      if (c.length === 4) return L.cmyk(c[0], c[1], c[2], c[3]);
      return L.rgb(0, 0, 0);
    }

    // Standard PDF fonts only cover Western European letters; drop anything else.
    function clean(s, role) {
      s = String(s);
      if (!STANDARD[role]) return s;
      var out = "";
      for (var i = 0; i < s.length; i++) {
        var ch = s.charAt(i);
        try { F[role].widthOfTextAtSize(ch, 10); out += ch; } catch (e) { out += "?"; }
      }
      return out;
    }

    function width(s, role, size) { return F[role].widthOfTextAtSize(clean(s, role), size); }

    function put(s, x, base, role, size, align, col) {
      if (s === null || s === undefined || s === "") return;
      s = clean(s, role);
      var w = F[role].widthOfTextAtSize(s, size);
      if (align === "r") x -= w;
      else if (align === "c") x -= w / 2;
      page.drawText(s, { x: x, y: H - base, size: size, font: F[role], color: color(col) });
    }

    function tick(cx, base, size, at) {
      var x = at ? at[0] + size / 2 : cx, b = at ? at[1] : base;
      var d = "M " + (x - 0.33 * size) + " " + (b - 0.38 * size) +
        " L " + (x - 0.10 * size) + " " + (b - 0.08 * size) +
        " L " + (x + 0.36 * size) + " " + (b - 0.78 * size);
      page.drawSvgPath(d, { x: 0, y: H, borderColor: L.rgb(0, 0, 0), borderWidth: 1.6,
        borderLineCap: L.LineCapStyle.Round });
    }

    function drawTemplate(tp) {
      tp.rects.forEach(function (r) {
        page.drawRectangle({ x: r.x0, y: H - r.bot, width: r.x1 - r.x0, height: r.bot - r.top,
          color: color(r.fill), borderWidth: 0 });
      });
      tp.lines.forEach(function (ln) {
        page.drawLine({ start: { x: ln.x0, y: H - ln.top }, end: { x: ln.x1, y: H - ln.bot },
          thickness: ln.lw, color: color(ln.color) });
      });
      tp.images.forEach(function (im) {
        page.drawImage(emblem, { x: im.x0, y: H - im.bot, width: im.x1 - im.x0, height: im.bot - im.top });
      });
      tp.words.forEach(function (w) {
        if (w.font === "taka") {
          // The bundled subset font draws the Taka sign at the "$" code point (this avoids
          // fontkit's Bengali shaper), and it comes out smaller than Tahoma's, so enlarge it.
          put(w.t.replace(/\u09f3/g, "$"), w.x, w.base, "taka", w.size * 1.35, "l", w.c);
          return;
        }
        put(w.t, w.x, w.base, w.font, w.size, "l", w.c);
      });
    }

    function fit(s, role, size, maxw) {
      while (size > 6 && width(s, role, size) > maxw) size -= 0.25;
      return size;
    }

    function wrap(s, role, size, maxw) {
      var lines = [], cur = "";
      s.split(/\s+/).forEach(function (word) {
        if (!word) return;
        var trial = cur ? cur + " " + word : word;
        if (width(trial, role, size) <= maxw || !cur) cur = trial;
        else { lines.push(cur); cur = word; }
      });
      if (cur) lines.push(cur);
      return lines;
    }

    function drawText(f, v) {
      var s = (v === null || v === undefined) ? "" : String(v).trim();
      if (!s) return;
      var role = f.font, size = f.size;
      if (f.lines > 1) {
        var lines = wrap(s, role, size, f.maxw);
        while (lines.length > f.lines && size > 6) { size -= 0.25; lines = wrap(s, role, size, f.maxw); }
        lines.slice(0, f.lines).forEach(function (line, i) {
          put(line, f.x, f.base + i * f.lead, role, size, f.align, f.color);
        });
        return;
      }
      put(s, f.x, f.base, role, fit(s, role, size, f.maxw), f.align, f.color);
    }

    function drawAmount(f, v) {
      if (v === null || v === undefined) return;
      var role = f.font, size = f.size;
      if (rnd(v) === 0) {
        if (f.zero === "blank") return;
        var right = f.dash ? f.dash : f.right - 2 * width("0", role, size);
        put("-", right, f.base, role, size, "r", f.color);
        return;
      }
      put(fmtAmount(v), f.right + (rnd(v) < 0 ? width(")", role, size) : 0), f.base, role, size, "r", f.color);
    }

    function drawField(f) {
      var v = V[f.key];
      switch (f.kind) {
        case "text": drawText(f, v); break;
        case "amount": drawAmount(f, v); break;
        case "digits":
          String(v || "").split("").forEach(function (ch, i) {
            if (i < f.centers.length) put(ch, f.centers[i], f.base, f.font, f.size, "c");
          });
          break;
        case "check":
          if (v) tick((f.box[0] + f.box[2]) / 2, f.box[3] - 3.6, 10.56, f.at);
          break;
        case "relation": {
          var x = f.x, parts = v === "husband"
            ? [["Father/", "serif"], ["Husband", "serif-bold"], [",", "serif"]]
            : [["Father", "serif-bold"], ["/Husband,", "serif"]];
          parts.forEach(function (p) { put(p[0], x, f.base, p[1], f.size, "l"); x += width(p[0], p[1], f.size); });
          break;
        }
        case "ornaments": {
          var qty = String(V["a.h_qty"] || ""), typ = String(V["a.h_type"] || ""), ox = f.x;
          if (qty) { put(qty + " ", ox, f.base, "serif-bold", f.size, "l"); ox += width(qty + " ", "serif-bold", f.size); }
          if (qty || V["a.h"]) put(typ, ox, f.base, "serif", f.size, "l");
          break;
        }
      }
    }

    A.template.pages.forEach(function (tp, i) {
      page = pdf.addPage([W, H]);
      drawTemplate(tp);
      A.fields[i].forEach(drawField);
    });

    pdf.setTitle(A.title || ("Return of Income - " + V.name + " - AY " + V.ay));
    pdf.setAuthor(V.name || "");
    pdf.setSubject("Return of income, assessment year " + (V.ay || ""));
    pdf.setCreator("BD e-Return");
    pdf.setProducer("BD e-Return (pdf-lib)");
    return await pdf.save();
  }

  /** Browser helper: load every data file the calculator and renderer need. */
  async function loadAssets(baseUrl, profileIds) {
    function get(path, kind) {
      return fetch(baseUrl + path, { credentials: "same-origin" }).then(function (r) {
        if (!r.ok) throw new Error("Could not load " + path + " (" + r.status + ")");
        return kind === "json" ? r.json() : r.arrayBuffer();
      });
    }
    var parts = await Promise.all([
      get("data/template.json", "json"), get("data/fields.json", "json"),
      get("img/emblem.png"), get("fonts/Carlito-Regular.ttf"), get("fonts/Carlito-Bold.ttf"),
      get("fonts/FreeSerif-taka-subset.ttf")
    ].concat(profileIds.map(function (id) { return get("data/rules/" + id + ".json", "json"); })));
    var profiles = {};
    profileIds.forEach(function (id, i) { profiles[id] = parts[6 + i]; });
    return {
      template: parts[0], fields: parts[1], emblem: parts[2], carlito: parts[3],
      carlitoBold: parts[4], taka: parts[5], profiles: profiles
    };
  }

  return { render: render, loadAssets: loadAssets, fmtAmount: fmtAmount };
});
