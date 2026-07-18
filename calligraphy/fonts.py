"""Single-stroke font loading for the strek calligraphy toolkit.

Two source formats, one Glyph model. Layout code (text2svg.py) consumes only
the Glyph model and never learns which format a Font came from:

  - classic Hershey ``.jhf``  (public domain, the "1960s pen" look)
  - EMS SVG fonts ``.svg``    (SIL OFL, calligraphic script)

Coordinate convention of the Glyph model: font units, **y-down** (same axis
sense as SVG and the rest of the pipeline), origin at the left side-bearing on
the baseline (baseline runs through ``Font.baseline``). Beziers/arcs from the
SVG fonts are flattened to polylines here so downstream code sees only
straight segments — which is also what scripts/svg2gcode.py accepts.
"""

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Glyph:
    char: str
    # Each stroke is one pen-down polyline: a list of (x, y) in font units.
    strokes: list = field(default_factory=list)
    advance: float = 0.0  # horizontal pen advance in font units


@dataclass
class Font:
    name: str
    fmt: str                       # "hershey" | "ems"
    glyphs: dict                   # char -> Glyph
    units_per_em: float
    cap_height: float              # font units, from top of caps to baseline
    baseline: float                # y (font units, y-down) of the writing line
    space_advance: float

    def glyph(self, char):
        """Glyph for char, falling back to space width for the unknown."""
        g = self.glyphs.get(char)
        if g is not None:
            return g
        return Glyph(char, [], self.space_advance)


def load_font(path):
    path = Path(path)
    if path.suffix.lower() == ".jhf":
        return _parse_hershey(path)
    if path.suffix.lower() == ".svg":
        return _parse_ems(path)
    raise ValueError(f"Unsupported font format: {path.suffix} ({path})")


# --------------------------------------------------------------------------
# Hershey .jhf
# --------------------------------------------------------------------------
# Record layout: 5-char glyph id, 3-char vertex count N (right-justified),
# then 2*N coordinate chars. Each coordinate char encodes value = ord(c) - 'R'.
# The first pair is (left, right) side bearings; the pen-up marker separating
# strokes is the pair " R" (a space in the x slot). Records may wrap across
# physical lines, so we parse from a single flattened character stream.

_R = ord("R")


def _parse_hershey(path):
    raw = path.read_text(encoding="latin-1")
    # Flatten to one stream but remember: newlines are not data. A record's
    # length is known from its vertex count, so we walk char-by-char.
    stream = raw.replace("\n", "").replace("\r", "")
    glyphs = {}
    i = 0
    index = 0  # nth glyph -> ASCII 32 + index (space first)
    n = len(stream)
    while i < n:
        # A record needs at least the 8-char header.
        if i + 8 > n:
            break
        header = stream[i : i + 8]
        try:
            verts = int(header[5:8])
        except ValueError:
            break
        i += 8
        coord_len = 2 * verts
        coords = stream[i : i + coord_len]
        i += coord_len

        char = chr(32 + index)
        index += 1
        glyphs[char] = _hershey_glyph(char, coords)

    return _finalize(path.stem, "hershey", glyphs)


def _hershey_glyph(char, coords):
    if len(coords) < 2:
        return Glyph(char, [], 0.0)
    left = ord(coords[0]) - _R
    right = ord(coords[1]) - _R
    advance = right - left
    strokes, cur = [], []
    j = 2
    while j + 1 < len(coords):
        cx, cy = coords[j], coords[j + 1]
        j += 2
        if cx == " ":  # pen up: end current stroke
            if len(cur) > 1:
                strokes.append(cur)
            cur = []
            continue
        x = (ord(cx) - _R) - left  # shift so left bearing sits at x=0
        y = ord(cy) - _R           # already y-down
        cur.append((float(x), float(y)))
    if len(cur) > 1:
        strokes.append(cur)
    return Glyph(char, strokes, float(advance))


# --------------------------------------------------------------------------
# EMS SVG fonts
# --------------------------------------------------------------------------
_SVG_NS = "{http://www.w3.org/2000/svg}"


def _parse_ems(path):
    root = ET.fromstring(path.read_text(encoding="utf-8"))

    def find(tag):
        return root.iter(_SVG_NS + tag)

    font_el = next(find("font"), None)
    face_el = next(find("font-face"), None)
    upm = float((face_el.get("units-per-em") if face_el else None) or 1000.0)
    cap = float((face_el.get("cap-height") if face_el else None) or (upm * 0.7))
    default_adv = float((font_el.get("horiz-adv-x") if font_el else None) or upm)

    glyphs = {}
    for g in find("glyph"):
        uni = g.get("unicode")
        if not uni or len(uni) != 1:
            continue  # skip ligatures / named-only glyphs
        adv = float(g.get("horiz-adv-x") or default_adv)
        strokes = _flatten_path(g.get("d", ""))
        # EMS glyphs are y-up with the baseline at 0; negate y for our y-down model.
        strokes = [[(x, -y) for (x, y) in s] for s in strokes]
        glyphs[uni] = Glyph(uni, strokes, adv)

    # Ensure a space glyph exists.
    if " " not in glyphs:
        glyphs[" "] = Glyph(" ", [], default_adv)

    return _finalize(path.stem, "ems", glyphs, upm=upm, cap=cap, baseline=0.0)


# --------------------------------------------------------------------------
# SVG path "d" -> flattened polylines
# --------------------------------------------------------------------------
_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")
# Flatten curves to line segments no longer than this many font units along the
# control polygon. EMS fonts use 1000 units/em, so ~18 keeps script curves
# smooth at any plot size without exploding the point count on tiny glyphs.
_FLAT = 18.0
_MIN_STEPS, _MAX_STEPS = 4, 72


def _steps(*pts):
    length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                 for i in range(len(pts) - 1))
    return max(_MIN_STEPS, min(_MAX_STEPS, int(length / _FLAT) + 1))


def _flatten_path(d):
    if not d:
        return []
    toks = _TOKEN.findall(d)
    strokes, cur = [], []
    i = 0
    x = y = 0.0
    sx = sy = 0.0            # subpath start
    cmd = None
    prev_ctrl = None        # for S/T smoothing
    prev_cmd = None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    def moveend():
        nonlocal cur
        if len(cur) > 1:
            strokes.append(cur)
        cur = []

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
        # else: implicit repeat of previous command
        rel = cmd.islower()
        c = cmd.upper()

        if c == "M":
            moveend()
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            sx, sy = x, y
            cur = [(x, y)]
            cmd = "l" if rel else "L"  # subsequent pairs are implicit lineto
        elif c == "L":
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            cur.append((x, y))
        elif c == "H":
            nx = num()
            x = x + nx if rel else nx
            cur.append((x, y))
        elif c == "V":
            ny = num()
            y = y + ny if rel else ny
            cur.append((x, y))
        elif c in ("C", "S"):
            if c == "C":
                x1, y1 = (x + num(), y + num()) if rel else (num(), num())
            else:  # smooth: reflect previous control point
                if prev_cmd in ("C", "S"):
                    x1, y1 = 2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1]
                else:
                    x1, y1 = x, y
            x2, y2 = (x + num(), y + num()) if rel else (num(), num())
            ex, ey = (x + num(), y + num()) if rel else (num(), num())
            _cubic(cur, x, y, x1, y1, x2, y2, ex, ey)
            prev_ctrl = (x2, y2)
            x, y = ex, ey
        elif c in ("Q", "T"):
            if c == "Q":
                x1, y1 = (x + num(), y + num()) if rel else (num(), num())
            else:  # smooth quadratic
                if prev_cmd in ("Q", "T"):
                    x1, y1 = 2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1]
                else:
                    x1, y1 = x, y
            ex, ey = (x + num(), y + num()) if rel else (num(), num())
            _quad(cur, x, y, x1, y1, ex, ey)
            prev_ctrl = (x1, y1)
            x, y = ex, ey
        elif c == "A":
            rx, ry = num(), num()
            rot = num(); large = num(); sweep = num()
            ex, ey = (x + num(), y + num()) if rel else (num(), num())
            _arc(cur, x, y, rx, ry, rot, large, sweep, ex, ey)
            x, y = ex, ey
        elif c == "Z":
            cur.append((sx, sy))
            x, y = sx, sy
        else:
            i += 1
            continue
        prev_cmd = c

    moveend()
    return strokes


def _cubic(out, x0, y0, x1, y1, x2, y2, x3, y3):
    n = _steps((x0, y0), (x1, y1), (x2, y2), (x3, y3))
    for k in range(1, n + 1):
        t = k / n
        u = 1 - t
        bx = u*u*u*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t*t*t*x3
        by = u*u*u*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t*t*t*y3
        out.append((bx, by))


def _quad(out, x0, y0, x1, y1, x2, y2):
    n = _steps((x0, y0), (x1, y1), (x2, y2))
    for k in range(1, n + 1):
        t = k / n
        u = 1 - t
        bx = u*u*x0 + 2*u*t*x1 + t*t*x2
        by = u*u*y0 + 2*u*t*y1 + t*t*y2
        out.append((bx, by))


def _arc(out, x0, y0, rx, ry, rot_deg, large, sweep, x1, y1):
    # Endpoint -> center parameterisation (SVG implementation notes F.6).
    if rx == 0 or ry == 0 or (x0 == x1 and y0 == y1):
        out.append((x1, y1))
        return
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(rot_deg)
    cosp, sinp = math.cos(phi), math.sin(phi)
    dx, dy = (x0 - x1) / 2.0, (y0 - y1) / 2.0
    x1p = cosp * dx + sinp * dy
    y1p = -sinp * dx + cosp * dy
    denom = rx*rx * y1p*y1p + ry*ry * x1p*x1p
    lam = (rx*rx * ry*ry) / denom if denom else 0.0
    if lam < 1e-12:
        out.append((x1, y1)); return
    num_ = rx*rx * ry*ry - denom
    co = math.sqrt(max(num_ / denom, 0.0))
    if large == sweep:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx
    cx = cosp * cxp - sinp * cyp + (x0 + x1) / 2.0
    cy = sinp * cxp + cosp * cyp + (y0 + y1) / 2.0

    def ang(ux, uy, vx, vy):
        d = math.hypot(ux, uy) * math.hypot(vx, vy)
        c = max(-1.0, min(1.0, (ux*vx + uy*vy) / d)) if d else 1.0
        a = math.acos(c)
        return -a if (ux*vy - uy*vx) < 0 else a

    theta0 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = ang((x1p - cxp) / rx, (y1p - cyp) / ry,
                 (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep and dtheta < 0:
        dtheta += 2 * math.pi

    steps = max(_MIN_STEPS, min(_MAX_STEPS,
                int(max(rx, ry) * abs(dtheta) / _FLAT) + 1))
    for k in range(1, steps + 1):
        th = theta0 + dtheta * k / steps
        ex = cosp * rx * math.cos(th) - sinp * ry * math.sin(th) + cx
        ey = sinp * rx * math.cos(th) + cosp * ry * math.sin(th) + cy
        out.append((ex, ey))


# --------------------------------------------------------------------------
# Shared finalisation
# --------------------------------------------------------------------------
def _finalize(name, fmt, glyphs, upm=None, cap=None, baseline=None):
    space = glyphs.get(" ")
    space_adv = space.advance if space else (upm or 32.0) * 0.3

    if fmt == "hershey":
        # Hershey files carry no metrics; derive the em from the data.
        upm = _hershey_em(glyphs)
        baseline = 9.0  # classic Hershey baseline, refined by 'H' below

    # Prefer the true cap-height of the actual 'H' glyph so --size means the
    # same physical height across both formats (EMS font-faces here omit the
    # cap-height attribute, and Hershey has no metrics at all). Baseline is the
    # bottom of 'H' — it has no descender, so it sits on the writing line.
    h = glyphs.get("H")
    if h and h.strokes:
        ys = [y for s in h.strokes for (_, y) in s]
        cap, baseline = (max(ys) - min(ys)), max(ys)
    elif cap is None:
        cap = (upm or 1000.0) * 0.7

    return Font(
        name=name, fmt=fmt, glyphs=glyphs,
        units_per_em=float(upm), cap_height=float(cap),
        baseline=float(baseline), space_advance=float(space_adv),
    )


def _hershey_em(glyphs):
    # Nominal Hershey em is ~ the full vertical extent; 32 units is the classic
    # design size, but measure from data to stay honest across variants.
    ys = [y for g in glyphs.values() for s in g.strokes for (_, y) in s]
    if not ys:
        return 32.0
    return max(ys) - min(ys)
