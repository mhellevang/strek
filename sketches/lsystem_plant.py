"""L-system: fraktalplante (Lindenmayers klassiker).

Turtle-tolkning: F = strek frem, +/- = sving, [ ] = push/pop posisjon.
Resultatet skaleres automatisk til å fylle siden.

Kjør:  uv run --with vsketch python sketches/lsystem_plant.py
Ut:    sketches/output/lsystem_plant.svg
"""

import math
import pathlib

import numpy as np
import vsketch

AXIOM = "X"
RULES = {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"}
ITERATIONS = 6
ANGLE = math.radians(25)
W, H = 160, 230  # mål-flate i mm

s = AXIOM
for _ in range(ITERATIONS):
    s = "".join(RULES.get(c, c) for c in s)

# turtle-walk: samle polylinjer (brutt ved push/pop)
x, y, heading = 0.0, 0.0, -math.pi / 2  # start rett opp
stack, lines, cur = [], [], [(x, y)]
for c in s:
    if c == "F":
        x += math.cos(heading)
        y += math.sin(heading)
        cur.append((x, y))
    elif c == "+":
        heading += ANGLE
    elif c == "-":
        heading -= ANGLE
    elif c == "[":
        stack.append((x, y, heading))
    elif c == "]":
        if len(cur) > 1:
            lines.append(cur)
        x, y, heading = stack.pop()
        cur = [(x, y)]
if len(cur) > 1:
    lines.append(cur)

# skaler til siden (uniform, bevarer proporsjoner)
allpts = np.concatenate([np.array(l) for l in lines])
lo, hi = allpts.min(axis=0), allpts.max(axis=0)
scale = min(W / (hi[0] - lo[0]), H / (hi[1] - lo[1]))

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")
for l in lines:
    vsk.polygon((np.array(l) - lo) * scale)

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "lsystem_plant.svg"))
print(f"Lagret {out / 'lsystem_plant.svg'} ({len(lines)} polylinjer)")
