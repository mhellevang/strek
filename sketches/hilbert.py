"""Hilbert-kurve: space-filling curve som L-system.

Én eneste sammenhengende strek som fyller hele flaten — null pennløft,
plotterens drømmedisiplin.

Kjør:  uv run --with vsketch python sketches/hilbert.py
Ut:    sketches/output/hilbert.svg
"""

import math
import pathlib

import vsketch

ORDER = 6        # 2^ORDER × 2^ORDER celler (6 → 64×64 = 4096 punkter)
SIZE = 160       # sidelengde i mm

RULES = {"A": "-BF+AFA+FB-", "B": "+AF-BFB-FA+"}
s = "A"
for _ in range(ORDER):
    s = "".join(RULES.get(c, c) for c in s)

step = SIZE / (2**ORDER - 1)
x, y, heading = 0.0, 0.0, 0.0
pts = [(x, y)]
for c in s:
    if c == "F":
        x += step * math.cos(heading)
        y += step * math.sin(heading)
        pts.append((x, y))
    elif c == "+":
        heading += math.pi / 2
    elif c == "-":
        heading -= math.pi / 2

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")
vsk.polygon(pts)

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "hilbert.svg"))
print(f"Lagret {out / 'hilbert.svg'} ({len(pts)} punkter, én strek)")
