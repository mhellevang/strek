"""Voronoi-diagram med noise-styrt punkttetthet — tettere celler der
perlin-feltet er høyt. Delte kanter tegnes kun én gang (viktig for
plotter: dobbelttegning gir mørkere strek).

Kjør:  uv run --with vsketch python sketches/voronoi.py
Ut:    sketches/output/voronoi.svg
"""

import pathlib

import numpy as np
import vsketch
from shapely.geometry import MultiPoint, box
from shapely.ops import voronoi_diagram

W, H = 170, 240
N_POINTS = 350
FREQ = 0.015
SEED = 9

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")
vsk.noiseSeed(SEED)
rng = np.random.default_rng(SEED)

# rejection sampling: aksepter punkt med sannsynlighet = noise^2
pts = []
while len(pts) < N_POINTS:
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    if rng.random() < vsk.noise(x * FREQ, y * FREQ) ** 2:
        pts.append((x, y))

omr = box(0, 0, W, H)
vd = voronoi_diagram(MultiPoint(pts), envelope=omr)

sett = set()
for cell in vd.geoms:
    klippet = cell.intersection(omr)
    polys = klippet.geoms if klippet.geom_type == "MultiPolygon" else [klippet]
    for poly in polys:
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        c = list(poly.exterior.coords)
        for p1, p2 in zip(c, c[1:]):
            a = (round(p1[0], 2), round(p1[1], 2))
            b = (round(p2[0], 2), round(p2[1], 2))
            key = (a, b) if a <= b else (b, a)
            if key not in sett:
                sett.add(key)
                vsk.line(p1[0], p1[1], p2[0], p2[1])

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "voronoi.svg"))
print(f"Lagret {out / 'voronoi.svg'} ({len(pts)} celler)")
