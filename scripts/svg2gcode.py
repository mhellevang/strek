#!/usr/bin/env python3
"""SVG to plotter G-code for a Bambu Lab P2S with the UMTS pen module.

Reads vpype-optimized SVGs (polygon/polyline/line) and generates G-code
with no extrusion: XY moves along the strokes, Z lifts between them.
(The web app in docs/ does the same in the browser and also accepts raw
SVGs with <path>/transforms.)

The drawing is centered on the PAPER, not just in the nozzle's legal
window: the sheet is assumed to sit in the alignment jig (29 mm from the
right wall, 41 mm from the back wall), and the pen tip sits at an XY
offset from the nozzle (--pen-dx/--pen-dy, assumed (-29, -41) from the
jig margins). Run --calibrate once and measure the cross on the sheet
before trusting the placement.

Safety (see README "Safety rules"):
  - No heating or E commands — heaters are actively turned OFF
    (M104 S0 / M140 S0), no E axis
  - All NOZZLE coordinates are validated against the legal window
    (outside the excluded area (0x0, 258x0, 258x55, 48x55, 48x258,
    0x258) + edge margin) — aborts with an error if anything falls
    outside. The window is convex, so all moves between approved points
    are safe too
  - Z never goes below --z-draw, and --z-draw below 16.0 mm is refused
    (the pen module needs ~17 mm clearance; 17.1 = pen barely on paper)
  - Homing happens WITHOUT the pen: the file starts with G28, parks the
    head near the front and pauses (M400 U1) — mount the pen, press
    resume on the screen

First run: --calibrate without the pen mounted and just watch (the
nozzle stays 17+ mm above the plate the whole time, harmless). Then pen
in, plot the cross, measure the deviation on the sheet and adjust
--pen-dx/--pen-dy.

Usage:
  python3 scripts/svg2gcode.py --calibrate                  # cross at paper center
  python3 scripts/svg2gcode.py file.svg                     # A4 sheet
  python3 scripts/svg2gcode.py file.svg --paper a5          # A5 landscape
  python3 scripts/svg2gcode.py file.svg --z-draw 17.3 --pen-dx -27
"""

import argparse
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "{http://www.w3.org/2000/svg}"
PX_TO_MM = 25.4 / 96.0  # vpype writes CSS px (96 dpi)

# Bed coordinates: X 0..256 (0 = left wall), Y 0..256 (0 = front).
# Legal NOZZLE window: the excluded area blocks x<48 and y<55 (module +
# walls/door), and we stay clear of the remaining edges.
X_MIN, X_MAX = 48.0, 255.0
Y_MIN, Y_MAX = 55.0, 255.0

Z_FLOOR = 16.0  # hard lower bound for z-draw — refused below this

# The sheet sits in the alignment jig: 29 mm from the right wall, 41 mm
# from the back wall (README "Paper position is critical"). If the jig
# changes, change this.
BED = 256.0
PAPER_RIGHT = BED - 29.0  # paper right edge, bed coordinate
PAPER_BACK = BED - 41.0   # paper back edge, bed coordinate

PAPERS = {"a4": (210.0, 297.0), "a5": (210.0, 148.0)}  # a5 = landscape


def parse_svg(path):
    """Returns (paths, scale_mm_per_unit). paths = list of [(x,y),...] in SVG coordinates."""
    tree = ET.parse(path)
    root = tree.getroot()

    # mm per SVG unit from width/viewBox (vpype: width in cm, viewBox in px)
    scale = PX_TO_MM
    viewbox = root.get("viewBox")
    width = root.get("width", "")
    if viewbox and width:
        vb_w = float(viewbox.split()[2])
        w, unit = _parse_length(width)
        if w and vb_w:
            scale = w / vb_w

    paths = []
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if el.get("transform") is not None:
            sys.exit(f"The SVG has a transform attribute on <{tag}> — coordinates "
                     "can't be read directly. Run it through "
                     "scripts/optimize.sh first (vpype bakes in transforms).")
        if tag in ("polygon", "polyline"):
            pts = _parse_points(el.get("points", ""))
            if tag == "polygon" and len(pts) > 1 and pts[0] != pts[-1]:
                pts.append(pts[0])  # close
            if len(pts) > 1:
                paths.append(pts)
        elif tag == "line":
            coords = [el.get(k) for k in ("x1", "y1", "x2", "y2")]
            if None in coords:
                sys.exit("The SVG has a <line> without x1/y1/x2/y2.")
            x1, y1, x2, y2 = map(float, coords)
            paths.append([(x1, y1), (x2, y2)])
        elif tag == "path":
            sys.exit("The SVG contains <path> elements — run it through "
                     "scripts/optimize.sh first (vpype flattens to polylines), "
                     "or use the web app, which samples paths natively.")
        elif tag in ("circle", "ellipse", "rect", "text", "image", "use"):
            sys.exit(f"The SVG contains <{tag}> — this script only reads "
                     "polygon/polyline/line. Run it through scripts/optimize.sh.")
    return paths, scale


def _parse_length(s):
    units = {"cm": 10.0, "mm": 1.0, "in": 25.4, "px": PX_TO_MM, "": PX_TO_MM}
    for unit in ("cm", "mm", "in", "px"):
        if s.endswith(unit):
            return float(s[: -len(unit)]) * units[unit], unit
    try:
        return float(s) * PX_TO_MM, "px"
    except ValueError:
        return None, None


def _parse_points(s):
    nums = s.replace(",", " ").split()
    return [(float(nums[i]), float(nums[i + 1])) for i in range(0, len(nums) - 1, 2)]


def _parse_paper(s):
    if s.lower() in PAPERS:
        return PAPERS[s.lower()]
    try:
        w, h = (float(v) for v in s.lower().split("x"))
        if w <= 0 or h <= 0:
            raise ValueError
        return (w, h)
    except ValueError:
        sys.exit(f"Unknown --paper \"{s}\" — use a4, a5 or WxH in mm (e.g. 148x105).")


def _clamp(v, lo, hi):
    if lo > hi:  # float rounding when the drawing fills the area exactly
        return (lo + hi) / 2
    return min(max(v, lo), hi)


def paper_rect(paper):
    """The sheet's extent in bed coordinates: (x0, x1, y0, y1)."""
    w, h = paper
    return (PAPER_RIGHT - w, PAPER_RIGHT, PAPER_BACK - h, PAPER_BACK)


def pen_window(args):
    """The area the pen tip can reach (nozzle window shifted by the pen offset)."""
    return (X_MIN + args.pen_dx, X_MAX + args.pen_dx,
            Y_MIN + args.pen_dy, Y_MAX + args.pen_dy)


def transform(paths, scale, args):
    """Scale to mm, flip Y (SVG y down, bed y toward the back), place on the paper.

    Placement happens in pen/bed coordinates: the target is the paper's
    center, clamped into the area the pen actually reaches. Scales DOWN
    only when needed — the design keeps its size if it fits. Returns
    NOZZLE coordinates (pen minus offset) ready for check_bounds()."""
    px0, px1, py0, py1 = paper_rect(args.paper)
    wx0, wx1, wy0, wy1 = pen_window(args)

    ux0, ux1 = max(px0, wx0) + args.margin, min(px1, wx1) - args.margin
    uy0, uy1 = max(py0, wy0) + args.margin, min(py1, wy1) - args.margin
    if ux1 <= ux0 or uy1 <= uy0:
        sys.exit("The drawable area is empty: paper ∩ pen window minus margin gives "
                 f"{ux1 - ux0:.0f}×{uy1 - uy0:.0f} mm. "
                 "Check --paper/--margin/--pen-dx/--pen-dy.")

    xs = [p[0] for path in paths for p in path]
    ys = [p[1] for path in paths for p in path]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w_mm = (max_x - min_x) * scale
    h_mm = (max_y - min_y) * scale

    fit = min((ux1 - ux0) / w_mm if w_mm else 1.0,
              (uy1 - uy0) / h_mm if h_mm else 1.0)
    s = scale * min(1.0, fit)
    if fit < 1.0:
        print(f"  NOTE: the design ({w_mm:.0f}×{h_mm:.0f} mm) exceeds the "
              f"drawable area ({ux1 - ux0:.0f}×{uy1 - uy0:.0f} mm) — "
              f"scaled down to {fit:.0%}")

    out_w = (max_x - min_x) * s
    out_h = (max_y - min_y) * s

    # Desired center = paper center; clamp to where the pen reaches
    cx = _clamp((px0 + px1) / 2, ux0 + out_w / 2, ux1 - out_w / 2)
    cy = _clamp((py0 + py1) / 2, uy0 + out_h / 2, uy1 - out_h / 2)
    if abs(cx - (px0 + px1) / 2) > 0.5 or abs(cy - (py0 + py1) / 2) > 0.5:
        print("  NOTE: the drawing can't sit at the paper's center (pen can't "
              "reach) — shifted to where the pen reaches, see margins below.")

    x_pen0, y_pen0 = cx - out_w / 2, cy - out_h / 2
    result = []
    for path in paths:
        result.append([
            (x_pen0 + (x - min_x) * s - args.pen_dx,   # pen → nozzle coordinate
             y_pen0 + (max_y - y) * s - args.pen_dy)   # Y flipped
            for x, y in path
        ])
    margins = (py1 - (cy + out_h / 2),  # top (toward the back wall)
               (cy - out_h / 2) - py0,  # bottom (toward the front)
               (cx - out_w / 2) - px0,  # left
               px1 - (cx + out_w / 2))  # right
    return result, out_w, out_h, margins


def calibration_paths(args):
    """Cross at the paper center + arrow toward the back wall. NOZZLE coordinates."""
    px0, px1, py0, py1 = paper_rect(args.paper)
    wx0, wx1, wy0, wy1 = pen_window(args)
    arm = 20.0
    cx = _clamp((px0 + px1) / 2, wx0 + arm + 5, wx1 - arm - 5)
    cy = _clamp((py0 + py1) / 2, wy0 + arm + 5, wy1 - arm - 5)
    paths = [
        [(cx - arm, cy), (cx + arm, cy)],
        [(cx, cy - arm), (cx, cy + arm)],
        [(cx - 5, cy + arm - 5), (cx, cy + arm), (cx + 5, cy + arm - 5)],  # arrow
    ]
    nozzle = [[(x - args.pen_dx, y - args.pen_dy) for x, y in p] for p in paths]
    return nozzle, (cx - (px0 + px1) / 2, cy - (py0 + py1) / 2)


def check_bounds(paths):
    for path in paths:
        for x, y in path:
            if not (X_MIN <= x <= X_MAX and Y_MIN <= y <= Y_MAX):
                sys.exit(f"SAFETY STOP: nozzle point ({x:.1f}, {y:.1f}) outside "
                         f"legal window X[{X_MIN},{X_MAX}] Y[{Y_MIN},{Y_MAX}]. "
                         "No G-code written.")


def generate(paths, args):
    z_up = args.z_draw + args.z_hop
    f_draw = int(args.draw_speed * 60)
    f_travel = int(args.travel_speed * 60)
    f_z = int(args.z_speed * 60)
    park_x, park_y = 152.0, 70.0  # near the front — easy to mount the pen
    src = args.svg.name if args.svg else "calibration cross"

    # per-path time cost first, so M73 progress is time-weighted
    costs, pos = [], (park_x, park_y)
    for path in paths:
        travel = math.dist(pos, path[0])
        draw = sum(math.dist(path[i], path[i + 1]) for i in range(len(path) - 1))
        costs.append(travel / args.travel_speed + draw / args.draw_speed
                     + 2 * args.z_hop / args.z_speed)
        pos = path[-1]
    total = sum(costs) or 1.0

    lines = [
        f"; Plotter G-code generated by strek — {src}",
        f"; z_draw={args.z_draw} z_hop={args.z_hop} draw={args.draw_speed}mm/s "
        f"travel={args.travel_speed}mm/s",
        f"; pen_dx={args.pen_dx} pen_dy={args.pen_dy} "
        f"paper={args.paper[0]:g}x{args.paper[1]:g}",
        "; NO heating, NO extrusion. Homes WITHOUT pen, pauses for pen mounting.",
        ";",
        "G21 ; millimeters",
        "G90 ; absolute coordinates",
        "M104 S0 ; hotend heater OFF",
        "M140 S0 ; bed heater OFF",
        "M106 S0 ; part fan off",
        "M106 P2 S0 ; aux fan off",
        "M106 P3 S0 ; chamber fan off",
        "G28 ; home all axes — PEN MUST NOT BE MOUNTED YET",
        f"G0 Z{z_up + 30:.1f} F{f_z}",
        f"G0 X{park_x:.0f} Y{park_y:.0f} F{f_travel} ; park near the front",
        "M400 U1 ; PAUSE: mount the pen, press resume",
        "M73 P0",
        f"G0 Z{z_up:.1f} F{f_z}",
    ]

    draw_len = travel_len = elapsed = 0.0
    pct = 0
    pos = (park_x, park_y)
    for path, cost in zip(paths, costs):
        x0, y0 = path[0]
        travel_len += math.dist(pos, (x0, y0))
        lines.append(f"G0 X{x0:.3f} Y{y0:.3f} F{f_travel}")
        lines.append(f"G1 Z{args.z_draw:.1f} F{f_z}")
        for x, y in path[1:]:
            lines.append(f"G1 X{x:.3f} Y{y:.3f} F{f_draw}")
            draw_len += math.dist((x0, y0), (x, y))
            x0, y0 = x, y
        lines.append(f"G0 Z{z_up:.1f} F{f_z}")
        pos = (x0, y0)
        elapsed += cost
        new_pct = min(99, int(100 * elapsed / total))
        if new_pct > pct:
            pct = new_pct
            lines.append(f"M73 P{pct}")

    lines += [
        f"G0 Z{z_up + 30:.1f} F{f_z}",
        f"G0 X{park_x:.0f} Y240 F{f_travel} ; head to the back — remove sheet/pen",
        "M400",
        "M73 P100",
        "; done",
    ]
    return "\n".join(lines) + "\n", draw_len, travel_len, total


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("svg", type=Path, nargs="?", help="vpype-optimized SVG")
    ap.add_argument("-o", "--out", type=Path, help="output file (.gcode)")
    ap.add_argument("--paper", default="a4",
                    help="paper size: a4, a5 (=210x148 landscape) or WxH in mm "
                         "(default a4). The sheet is assumed to sit in the "
                         "alignment jig: 29 mm from the right wall, 41 mm from "
                         "the back wall")
    ap.add_argument("--pen-dx", type=float, default=-29.0,
                    help="pen tip X offset from the nozzle, mm (default -29 — "
                         "ASSUMED from the jig margins, verify with --calibrate)")
    ap.add_argument("--pen-dy", type=float, default=-41.0,
                    help="pen tip Y offset from the nozzle, mm (default -41 — "
                         "ASSUMED, verify with --calibrate)")
    ap.add_argument("--calibrate", action="store_true",
                    help="generate a calibration cross at the paper center instead of an SVG")
    ap.add_argument("--z-draw", type=float, default=17.1,
                    help="Z where the pen draws (default 17.1 = Stabilo module +17 "
                         "plus paper; calibrate in 0.1 steps)")
    ap.add_argument("--z-hop", type=float, default=3.0, help="pen lift in mm (default 3)")
    ap.add_argument("--draw-speed", type=float, default=150.0,
                    help="draw speed mm/s (default 150; Stabilo takes 300–400)")
    ap.add_argument("--travel-speed", type=float, default=200.0, help="travel speed mm/s")
    ap.add_argument("--z-speed", type=float, default=15.0, help="Z speed mm/s")
    ap.add_argument("--margin", type=float, default=5.0,
                    help="extra margin inside the drawable area, mm (default 5)")
    args = ap.parse_args()

    if args.z_draw < Z_FLOOR:
        sys.exit(f"SAFETY STOP: --z-draw {args.z_draw} < {Z_FLOOR} mm. "
                 "The pen module needs ~17 mm clearance — this would press "
                 "the module into the plate.")
    if args.z_draw < 17.0:
        print(f"  NOTE: --z-draw {args.z_draw} is below 17.0 — heavy pen pressure. "
              "The spring absorbs it, but make sure it's intended.")
    if args.z_hop <= 0:
        sys.exit(f"SAFETY STOP: --z-hop {args.z_hop} must be > 0 — otherwise "
                 "the pen drags across the sheet between paths.")
    for name in ("draw_speed", "travel_speed", "z_speed"):
        if getattr(args, name) <= 0:
            sys.exit(f"--{name.replace('_', '-')} must be > 0.")
    if args.margin < 0:
        sys.exit("--margin must be ≥ 0.")
    args.paper = _parse_paper(args.paper)

    if args.calibrate:
        machine_paths, (miss_x, miss_y) = calibration_paths(args)
        check_bounds(machine_paths)
        gcode, _, _, _ = generate(machine_paths, args)
        out = args.out or Path("calibration-cross.gcode")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(gcode)
        print(f"Wrote {out}")
        print(f"  Cross at the center of the {args.paper[0]:g}×{args.paper[1]:g} sheet, "
              "arrow pointing toward the back wall.")
        if abs(miss_x) > 0.5 or abs(miss_y) > 0.5:
            print(f"  NOTE: the paper center is out of pen reach — the cross is "
                  f"shifted ({miss_x:+.0f}, {miss_y:+.0f}) mm from center. "
                  "Measure against its expected position, not the center.")
        print("  Measure on the sheet afterwards:")
        print(f"    cross N mm too far RIGHT          → --pen-dx {args.pen_dx:g} + N")
        print(f"    cross N mm too far toward the BACK → --pen-dy {args.pen_dy:g} + N")
        print("    (toward the left/front: subtract N)")
        return

    if not args.svg:
        ap.error("give an SVG file, or use --calibrate")
    paths, scale = parse_svg(args.svg)
    if not paths:
        sys.exit("No strokes found in the SVG.")
    machine_paths, w, h, margins = transform(paths, scale, args)
    check_bounds(machine_paths)

    gcode, draw_len, travel_len, est = generate(machine_paths, args)
    out = args.out or args.svg.with_suffix(".gcode")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(gcode)

    print(f"Wrote {out}")
    print(f"  {len(machine_paths)} paths, drawing {w:.0f}×{h:.0f} mm on a "
          f"{args.paper[0]:g}×{args.paper[1]:g} mm sheet")
    print(f"  margins on the sheet: top {margins[0]:.0f} / bottom {margins[1]:.0f} / "
          f"left {margins[2]:.0f} / right {margins[3]:.0f} mm")
    print(f"  ink {draw_len / 1000:.1f} m, travel {travel_len / 1000:.1f} m")
    print(f"  estimated plot time ~{est / 60:.0f} min without acceleration — "
          "many short segments can take 2–3× longer")


if __name__ == "__main__":
    main()
