"""Joy Division / "Unknown Pleasures"-landskap.

Horisontale noise-linjer med gaussisk amplitude-konvolutt i midten og
okklusjon: linjer foran skjuler linjer bak, som på plateomslaget.

Kjør:  uv run --with vsketch python sketches/joy_division.py
Ut:    sketches/output/joy_division.svg  (A4, mm — klar for optimaliser.sh)
"""

import pathlib

import numpy as np
import vsketch

W, H = 150, 180  # tegneflate i mm
ROWS = 45        # antall linjer
STEP = 1.0       # x-oppløsning i mm
AMP = 35         # makshøyde på toppene i mm
SEED = 42

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")
vsk.noiseSeed(SEED)

xs = np.arange(0, W + STEP, STEP)
envelope = np.exp(-((xs - W / 2) ** 2) / (2 * (W / 7) ** 2))
horizon = np.full(len(xs), np.inf)  # laveste y tegnet så langt per x

spacing = H / ROWS
for i in range(ROWS - 1, -1, -1):  # forfra (nederst) og bakover
    y_base = i * spacing
    seg = []
    for j, x in enumerate(xs):
        n = vsk.noise(x * 0.035, i * 0.25)
        y = y_base - (1.5 + AMP * envelope[j]) * n**2  # ^2 gir spissere topper
        if y < horizon[j] - 0.15:  # synlig kun over alle linjer foran
            seg.append((x, y))
        else:
            if len(seg) > 1:
                vsk.polygon(seg)
            seg = []
        horizon[j] = min(horizon[j], y)
    if len(seg) > 1:
        vsk.polygon(seg)

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "joy_division.svg"))
print(f"Lagret {out / 'joy_division.svg'}")
