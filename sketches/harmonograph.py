"""Harmonograf: dempede lissajous-kurver — simulerer det gamle
pendel-tegneapparatet. Nesten ingen kode, matematisk pent resultat.

Frekvensene er nesten-heltall; detuningen (3.001 vs 3) gir den sakte
presesjonen som lager dybden i mønsteret.

Kjør:  uv run --with vsketch python sketches/harmonograph.py
Ut:    sketches/output/harmonograph.svg
"""

import pathlib

import numpy as np
import vsketch

A = 55           # amplitude i mm
T_MAX = 250      # lengde på "pendelslippet"
N = 40000        # samplingspunkter
SEED = 1         # brukes kun hvis RANDOM = True
RANDOM = False   # True: trekk tilfeldige frekvenser/faser

f1, f2, f3, f4 = 3.001, 2.0, 3.0, 2.005
p1, p2, p3, p4 = np.pi / 2, 0.0, 0.0, np.pi / 2
d1, d2, d3, d4 = 0.006, 0.0065, 0.008, 0.0055

if RANDOM:
    rng = np.random.default_rng(SEED)
    f1, f3 = rng.integers(2, 6) + rng.normal(0, 0.002, 2)
    f2, f4 = rng.integers(2, 6) + rng.normal(0, 0.002, 2)
    p1, p2, p3, p4 = rng.uniform(0, 2 * np.pi, 4)

t = np.linspace(0, T_MAX, N)
x = A * np.sin(f1 * t + p1) * np.exp(-d1 * t) + A * np.sin(f2 * t + p2) * np.exp(-d2 * t)
y = A * np.sin(f3 * t + p3) * np.exp(-d3 * t) + A * np.sin(f4 * t + p4) * np.exp(-d4 * t)

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")
vsk.polygon(zip(x, y))

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "harmonograph.svg"))
print(f"Lagret {out / 'harmonograph.svg'}")
