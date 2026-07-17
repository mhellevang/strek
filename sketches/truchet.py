"""Truchet-fliser: rutenett der hver celle får to kvartsirkelbuer,
tilfeldig rotert. Buene kobler seg til nabocellene og danner
sammenhengende slyngmønstre. To lag = to penner (én per flisvariant).

Kjør:  uv run --with vsketch python sketches/truchet.py
Ut:    sketches/output/truchet.svg
"""

import pathlib

import numpy as np
import vsketch

CELL = 10        # flisstørrelse i mm
COLS, ROWS = 16, 22
SEED = 11

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")
rng = np.random.default_rng(SEED)

r = CELL / 2
a = np.linspace(0, np.pi / 2, 12)  # kvartsirkel som polylinje
cos_a, sin_a = r * np.cos(a), r * np.sin(a)

for i in range(COLS):
    for j in range(ROWS):
        x0, y0 = i * CELL, j * CELL
        x1, y1 = x0 + CELL, y0 + CELL
        if rng.random() < 0.5:  # variant A: buer i øvre-venstre + nedre-høyre
            vsk.stroke(1)
            vsk.polygon(zip(x0 + cos_a, y0 + sin_a))
            vsk.polygon(zip(x1 - cos_a, y1 - sin_a))
        else:                   # variant B: øvre-høyre + nedre-venstre
            vsk.stroke(2)
            vsk.polygon(zip(x1 - cos_a, y0 + sin_a))
            vsk.polygon(zip(x0 + cos_a, y1 - sin_a))

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "truchet.svg"))
print(f"Lagret {out / 'truchet.svg'}")
