"""Flow field: partikler følger et perlin-noise-vinkelfelt.

Tre lag (= tre penner) fordelt etter feltverdien der streken starter,
så fargene følger feltets regioner. Plott lag for lag, lys først.

Kjør:  uv run --with vsketch python sketches/flow_field.py
Ut:    sketches/output/flow_field.svg  (A4, mm — klar for optimaliser.sh)
"""

import math
import pathlib

import numpy as np
import vsketch

W, H = 170, 240   # tegneflate i mm
N_LINES = 600     # antall strøk
STEP = 1.2        # steglengde i mm
MAX_STEPS = 150   # maks lengde per strøk
FREQ = 0.012      # noise-frekvens: lavere = rolige buer, høyere = kaos
SWIRL = 4 * math.pi  # vinkelspenn: 2π = rolig, 4π = mer virvling
LAYERS = 3        # antall penner/lag
SEED = 7

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")
vsk.noiseSeed(SEED)
rng = np.random.default_rng(SEED)

strokes = []
for _ in range(N_LINES):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    pts = [(x, y)]
    for _ in range(MAX_STEPS):
        a = vsk.noise(x * FREQ, y * FREQ) * SWIRL
        x += STEP * math.cos(a)
        y += STEP * math.sin(a)
        if not (0 <= x <= W and 0 <= y <= H):
            break
        pts.append((x, y))
    if len(pts) > 3:
        # feltverdi ved startpunktet (z=100 gir uavhengig felt) styrer lagvalg
        n = vsk.noise(pts[0][0] * FREQ, pts[0][1] * FREQ, 100)
        strokes.append((n, pts))

# kvantil-split i stedet for n*LAYERS: perlin klumper seg rundt 0.5,
# kvantiler gir like mange strøk per penn
cuts = np.quantile([n for n, _ in strokes], np.linspace(0, 1, LAYERS + 1)[1:-1])
for n, pts in strokes:
    vsk.stroke(1 + int(np.searchsorted(cuts, n)))
    vsk.polygon(pts)

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "flow_field.svg"))
print(f"Lagret {out / 'flow_field.svg'}")
