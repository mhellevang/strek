#!/usr/bin/env python3
"""text2svg — turn a text string into a single-stroke, plottable SVG.

The output is bare <polyline> geometry with absolute coordinates in real
millimetres (no <path>, no transform), so it feeds straight into the strek
pipeline: scripts/optimize.sh -> scripts/svg2gcode.py (or the web app).

This tool is deliberately paper-agnostic: --size sets the cap-height in mm and
svg2gcode.py owns paper size, placement and bounds (see
docs/adr/0001-calligraphy-toolkit-is-paper-agnostic.md).

Examples:
  python3 calligraphy/text2svg.py "hei" --font EMSAllure --size 14
  python3 calligraphy/text2svg.py --font HersheyScript1 dikt.txt -o out.svg
  echo "flere\nlinjer" | python3 calligraphy/text2svg.py --font EMSDelight -
"""

import argparse
import re
import sys
from pathlib import Path

import fonts as fontlib

FONT_DIRS = [Path(__file__).parent / "fonts" / "ems",
             Path(__file__).parent / "fonts" / "hershey"]
OUTPUT_DIR = Path(__file__).parent / "output"


# --------------------------------------------------------------------------
# Font discovery
# --------------------------------------------------------------------------
def available_fonts():
    """{stem: path} for every vendored font, ems + hershey."""
    found = {}
    for d in FONT_DIRS:
        for f in sorted(d.glob("*")):
            if f.suffix.lower() in (".svg", ".jhf"):
                found[f.stem] = f
    return found


def resolve_font(name):
    fonts = available_fonts()
    if name in fonts:
        return fonts[name]
    lower = {k.lower(): v for k, v in fonts.items()}
    if name.lower() in lower:
        return lower[name.lower()]
    raise SystemExit(
        f'Unknown font "{name}". Try --list-fonts.')


def list_fonts():
    for d in FONT_DIRS:
        for f in sorted(d.glob("*")):
            if f.suffix.lower() in (".svg", ".jhf"):
                print(f"  {f.stem:<22} {d.name}")


# --------------------------------------------------------------------------
# Layout — Glyphs -> strokes in mm
# --------------------------------------------------------------------------
def layout(text, font, size_mm, line_height_mm, letter_spacing_mm):
    """Return (strokes_mm, width_mm, height_mm).

    All placement happens in font units first, then a single scale to mm.
    """
    scale = size_mm / font.cap_height  # cap-height -> requested mm
    lh_units = line_height_mm / scale
    ls_units = letter_spacing_mm / scale

    lines = text.split("\n")
    placed = []  # strokes in font units, y-down, baseline of line 0 at y=0
    for li, line in enumerate(lines):
        pen = 0.0
        line_base = li * lh_units
        for ch in line:
            g = font.glyph(ch)
            for stroke in g.strokes:
                placed.append([(pen + gx, (gy - font.baseline) + line_base)
                               for (gx, gy) in stroke])
            pen += g.advance + ls_units

    if not placed:
        return [], 0.0, 0.0

    # Scale to mm and normalise so the drawing starts at the origin.
    xs = [x for s in placed for (x, _) in s]
    ys = [y for s in placed for (_, y) in s]
    minx, miny = min(xs), min(ys)
    strokes_mm = [[((x - minx) * scale, (y - miny) * scale) for (x, y) in s]
                  for s in placed]
    width = (max(xs) - minx) * scale
    height = (max(ys) - miny) * scale
    return strokes_mm, width, height


# --------------------------------------------------------------------------
# Smoothing
# --------------------------------------------------------------------------
def chaikin(stroke, iters):
    """Endpoint-preserving Chaikin corner-cutting.

    The vendored EMS script fonts are stored as coarse polylines, so their
    curves come out faceted. Chaikin rounds the interior corners while pinning
    the two endpoints, turning the polygonal chain into a smooth pen path.
    """
    pts = stroke
    for _ in range(iters):
        if len(pts) < 3:
            break
        out = [pts[0]]
        for i in range(len(pts) - 1):
            (px, py), (qx, qy) = pts[i], pts[i + 1]
            out.append((0.75 * px + 0.25 * qx, 0.75 * py + 0.25 * qy))
            out.append((0.25 * px + 0.75 * qx, 0.25 * py + 0.75 * qy))
        out.append(pts[-1])
        pts = out
    return pts


# --------------------------------------------------------------------------
# SVG output
# --------------------------------------------------------------------------
def to_svg(strokes_mm, width_mm, height_mm, margin_mm=2.0):
    w = width_mm + 2 * margin_mm
    h = height_mm + 2 * margin_mm

    def fmt(v):
        return f"{v:.3f}".rstrip("0").rstrip(".")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{fmt(w)}mm" height="{fmt(h)}mm" '
        f'viewBox="0 0 {fmt(w)} {fmt(h)}">',
        '<g fill="none" stroke="black" stroke-width="0.3" '
        'stroke-linecap="round" stroke-linejoin="round">',
    ]
    for stroke in strokes_mm:
        pts = " ".join(f"{fmt(x + margin_mm)},{fmt(y + margin_mm)}"
                       for (x, y) in stroke)
        lines.append(f'<polyline points="{pts}"/>')
    lines.append("</g>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Input / output plumbing
# --------------------------------------------------------------------------
def read_text(arg):
    """Positional string, else a file path, else stdin ('-' or omitted)."""
    if arg is None or arg == "-":
        return sys.stdin.read().rstrip("\n")
    p = Path(arg)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8").rstrip("\n")
    return arg  # treat as a literal string


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:40] or "text")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="text2svg",
        description="Text -> single-stroke plottable SVG for the strek pipeline.")
    ap.add_argument("text", nargs="?",
                    help="Text, or a path to a .txt file. Omit to read stdin.")
    ap.add_argument("--font", default="EMSAllure",
                    help="Font name (see --list-fonts). Default: EMSAllure.")
    ap.add_argument("--size", type=float, default=10.0,
                    help="Cap-height in mm. Default: 10.")
    ap.add_argument("--line-height", type=float, default=None,
                    help="Line spacing in mm. Default: 1.8 * size.")
    ap.add_argument("--letter-spacing", type=float, default=0.0,
                    help="Extra space between glyphs in mm. Default: 0.")
    ap.add_argument("--smooth", type=int, default=2,
                    help="Chaikin smoothing passes (rounds the coarse font "
                         "polylines). 0 = faithful; try 0 for gothic. Default: 2.")
    ap.add_argument("-o", "--output", default=None,
                    help="Output path, or '-' for stdout. "
                         "Default: calligraphy/output/<slug>.svg.")
    ap.add_argument("--list-fonts", action="store_true",
                    help="List available fonts and exit.")
    args = ap.parse_args(argv)

    if args.list_fonts:
        list_fonts()
        return 0

    text = read_text(args.text)
    if not text.strip():
        raise SystemExit("No text given.")

    font = fontlib.load_font(resolve_font(args.font))
    line_h = args.line_height if args.line_height is not None else 1.8 * args.size
    strokes, w, h = layout(text, font, args.size, line_h, args.letter_spacing)
    if not strokes:
        raise SystemExit("Nothing to draw (no glyphs matched the text).")
    if args.smooth > 0:
        strokes = [chaikin(s, args.smooth) for s in strokes]
    svg = to_svg(strokes, w, h)

    if args.output == "-":
        sys.stdout.write(svg)
        return 0
    out = Path(args.output) if args.output else OUTPUT_DIR / f"{slugify(text)}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    n = sum(len(s) for s in strokes)
    print(f"Wrote {out}  ({len(strokes)} strokes, {n} points, "
          f"{w:.1f}x{h:.1f} mm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
