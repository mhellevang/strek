#!/usr/bin/env python3
"""build_gallery — render one sample phrase in every vendored font into a
self-contained docs/fonts.html gallery.

Static by design: this bakes the strokes at build time so the page needs no
JS font engine and works as a plain GitHub Pages file. Re-run whenever a font
is added or the sample phrase changes:

    python3 calligraphy/build_gallery.py
    python3 calligraphy/build_gallery.py --phrase "Kjære deg"

Each card shows the same phrase so the fonts can be compared side by side.
Hershey fonts are ASCII-only, so æøå fall out — the card flags that.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # text2svg imports `fonts` as a sibling module

import fonts as fontlib          # noqa: E402
import text2svg as t2s           # noqa: E402

DOCS = HERE.parent / "docs"
DEFAULT_PHRASE = "Blåbær på fløte"
SIZE_MM = 12.0
SMOOTH = 2
MARGIN_MM = 2.0

# The æøå the Norwegian phrase needs; used to flag fonts that lack them.
NORDIC = "æøåÆØÅ"


def fmt(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


def render_inline_svg(strokes_mm, w, h):
    """Bare <svg> (no XML prolog) with strokes in currentColor so the gallery
    inherits the page's ink color and adapts to light/dark themes."""
    vw, vh = w + 2 * MARGIN_MM, h + 2 * MARGIN_MM
    parts = [
        f'<svg viewBox="0 0 {fmt(vw)} {fmt(vh)}" '
        f'preserveAspectRatio="xMidYMid meet" role="img">',
        '<g fill="none" stroke="currentColor" stroke-width="0.3" '
        'stroke-linecap="round" stroke-linejoin="round">',
    ]
    for stroke in strokes_mm:
        pts = " ".join(f"{fmt(x + MARGIN_MM)},{fmt(y + MARGIN_MM)}"
                       for (x, y) in stroke)
        parts.append(f'<polyline points="{pts}"/>')
    parts.append("</g></svg>")
    return "".join(parts)


def dump_fonts_json():
    """Serialize every font's pre-flattened glyphs + metrics to one JSON blob.

    The browser tool (docs/text.html) does layout on these directly, so all the
    bezier/arc flattening stays here in Python and never needs a JS port. Coords
    are font units, y-down — the same model text2svg.layout() consumes.
    """
    import json

    def r(v):  # 1 decimal is ~0.01 mm at plot size — well below pen width
        return round(v, 1)

    fonts = {}
    for name, path in sorted(t2s.available_fonts().items()):
        f = fontlib.load_font(path)
        glyphs = {}
        for ch, g in f.glyphs.items():
            glyphs[ch] = {
                "adv": r(g.advance),
                "strokes": [[[r(x), r(y)] for (x, y) in s] for s in g.strokes],
            }
        fonts[name] = {
            "fmt": f.fmt,
            "unitsPerEm": r(f.units_per_em),
            "capHeight": r(f.cap_height),
            "baseline": r(f.baseline),
            "spaceAdvance": r(f.space_advance),
            "glyphs": glyphs,
        }
    return json.dumps(fonts, ensure_ascii=False, separators=(",", ":"))


def font_cards(phrase):
    cards = []
    for name, path in sorted(t2s.available_fonts().items()):
        font = fontlib.load_font(path)
        missing = sorted({c for c in phrase if c in NORDIC
                          and c not in font.glyphs})
        line_h = 1.8 * SIZE_MM
        strokes, w, h = t2s.layout(phrase, font, SIZE_MM, line_h, 0.0)
        if not strokes:
            continue
        if SMOOTH > 0:
            strokes = [t2s.chaikin(s, SMOOTH) for s in strokes]
        svg = render_inline_svg(strokes, w, h)
        fmt_label = "Hershey" if font.name.startswith("Hershey") else "EMS"
        npts = sum(len(s) for s in strokes)
        badge = ""
        if missing:
            badge = (f'<span class="badge">ASCII only — mangler '
                     f'{"".join(missing)}</span>')
        cards.append(f"""      <figure class="card">
        <div class="art">{svg}</div>
        <figcaption>
          <span class="fname">{name}</span>
          <span class="meta">{fmt_label} · {len(strokes)} strøk · {npts} pkt</span>
          {badge}
        </figcaption>
      </figure>""")
    return cards


def build_html(phrase, cards):
    body = "\n".join(cards)
    return f"""<!doctype html>
<html lang="no">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>strek — font-galleri</title>
<meta name="description" content="Enkeltstrøk-fonter i strek-kalligrafi-toolkitet, samme frase i hver font.">
<style>
  :root {{
    --paper: #FBFBF8; --sheet: #FFFFFF; --ink: #1C2740; --muted: #5B6675;
    --rule: #C9CFD8; --grid: #E7EBF0; --blue: #2B50C8; --amber: #9A6A08;
    --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace;
    --sans: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --paper: #14161B; --sheet: #1B1E25; --ink: #E7EBF2;
      --muted: #97A0B0; --rule: #333A46; --grid: #262B33; --blue: #7E9BFF; }}
  }}
  * {{ box-sizing: border-box; margin: 0; }}
  html, body {{ background: var(--paper); color: var(--ink); }}
  body {{ font-family: var(--sans); font-size: 15px; line-height: 1.45; padding: 20px; }}
  .sheet {{ max-width: 1180px; margin: 0 auto; border: 1.5px solid var(--ink);
    outline: 1px solid var(--ink); outline-offset: 3px; background: var(--paper);
    padding: 26px 28px; }}
  header {{ display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap;
    margin-bottom: 6px; }}
  h1 {{ font-family: var(--mono); font-size: 24px; font-weight: 600;
    letter-spacing: 0.24em; text-transform: uppercase; }}
  h1 .caret {{ color: var(--blue); }}
  .tagline {{ font-family: var(--mono); font-size: 12px; color: var(--muted);
    letter-spacing: 0.04em; }}
  .phrase {{ font-family: var(--mono); font-size: 12px; color: var(--muted);
    border-top: 1px solid var(--rule); margin-top: 14px; padding-top: 12px; }}
  .phrase b {{ color: var(--ink); }}
  .grid {{ display: grid; gap: 18px; margin-top: 18px;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }}
  .card {{ border: 1px solid var(--rule); background: var(--sheet); }}
  .art {{ padding: 18px 20px; min-height: 96px; display: flex;
    align-items: center; justify-content: center; }}
  .art svg {{ width: 100%; height: auto; max-height: 120px; color: var(--ink); }}
  figcaption {{ border-top: 1px solid var(--rule); padding: 8px 12px 10px;
    display: flex; flex-direction: column; gap: 2px; }}
  .fname {{ font-family: var(--mono); font-size: 14px; }}
  .meta {{ font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.04em;
    color: var(--muted); text-transform: uppercase; }}
  .badge {{ align-self: flex-start; margin-top: 4px; font-family: var(--mono);
    font-size: 10px; color: var(--amber); border: 1px solid var(--amber);
    padding: 1px 6px; }}
  footer {{ margin-top: 22px; border-top: 1px solid var(--ink); padding-top: 12px;
    display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap;
    font-family: var(--mono); font-size: 11.5px; color: var(--muted); }}
  footer a {{ color: var(--blue); }}
</style>
</head>
<body>
<div class="sheet">
  <header>
    <h1>strek<span class="caret">_</span> font-galleri</h1>
    <p class="tagline">enkeltstrøk-fonter · samme frase i hver font</p>
  </header>
  <p class="phrase">Frase: <b>{phrase}</b> · cap-høyde {fmt(SIZE_MM)} mm · generert av
    <code>calligraphy/build_gallery.py</code>. Skriv egen tekst:
    <code>python3 calligraphy/text2svg.py "…" --font &lt;navn&gt;</code></p>

  <div class="grid">
{body}
  </div>

  <footer>
    <a href="index.html">&#8592; tilbake til strek-generatoren</a>
    <span><a href="text.html">tekst &#8594; SVG</a> &#183; <a href="https://github.com/mhellevang/strek">github.com/mhellevang/strek</a></span>
  </footer>
</div>
</body>
</html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phrase", default=DEFAULT_PHRASE,
                    help=f"sample phrase (default {DEFAULT_PHRASE!r})")
    ap.add_argument("-o", "--output", default=str(DOCS / "fonts.html"),
                    help="output HTML path (default docs/fonts.html)")
    args = ap.parse_args(argv)

    cards = font_cards(args.phrase)
    if not cards:
        raise SystemExit("No fonts rendered — check calligraphy/fonts/.")
    out = Path(args.output)
    out.write_text(build_html(args.phrase, cards), encoding="utf-8")
    print(f"Wrote {out}  ({len(cards)} fonts, phrase {args.phrase!r})")

    fonts_json = out.parent / "fonts.json"
    fonts_json.write_text(dump_fonts_json(), encoding="utf-8")
    kb = fonts_json.stat().st_size / 1024
    print(f"Wrote {fonts_json}  ({kb:.0f} KB — glyph data for docs/text.html)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
