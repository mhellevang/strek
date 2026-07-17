"""Circle packing: tilfeldige kandidater vokser til de treffer nabo
eller kant. Tre lag etter størrelse = tre penner (store sirkler lys
penn, små mørk gir dybde).

Kjør:  uv run --with vsketch python sketches/circle_packing.py
Ut:    sketches/output/circle_packing.svg
"""

import pathlib

import numpy as np
import vsketch

W, H = 170, 240
ATTEMPTS = 4000
R_MIN, R_MAX = 1.0, 22.0
GAP = 0.6  # luft mellom sirkler i mm
SEED = 5

rng = np.random.default_rng(SEED)
cx, cy, cr = np.empty(0), np.empty(0), np.empty(0)

for _ in range(ATTEMPTS):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    r_wall = min(x, y, W - x, H - y)
    r = min(rng.uniform(R_MIN, R_MAX), r_wall)
    if len(cx):
        d = np.hypot(cx - x, cy - y) - cr - GAP
        if (d <= 0).any():
            continue
        r = min(r, d.min())
    if r >= R_MIN:
        cx, cy, cr = np.append(cx, x), np.append(cy, y), np.append(cr, r)

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")

terskler = np.quantile(cr, [1 / 3, 2 / 3])
for x, y, r in zip(cx, cy, cr):
    vsk.stroke(1 + int(np.searchsorted(terskler, r)))
    vsk.circle(x, y, radius=r)
    if r > 8:  # konsentriske ringer i de store
        vsk.circle(x, y, radius=r * 0.6)
        vsk.circle(x, y, radius=r * 0.3)

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "circle_packing.svg"))
print(f"Lagret {out / 'circle_packing.svg'} ({len(cx)} sirkler)")
