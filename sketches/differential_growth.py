"""Differential growth: lukket kurve som vokser organisk.

Hver node tiltrekkes naboene sine (holder kurven sammen) og frastøtes
alle noder nær seg (tvinger folder). Kanter som strekkes deles i to —
kurven vokser til koral/hjernemønster. Snapshot hver N-te iterasjon
gir konsentriske vekstringer.

Kjør:  uv run --with vsketch python sketches/differential_growth.py
Ut:    sketches/output/differential_growth.svg
"""

import pathlib

import numpy as np
import vsketch

R_REP = 4.0      # frastøtingsradius i mm
F_REP = 0.80     # frastøtingsstyrke
F_ATT = 0.12     # nabotiltrekning
SPLIT = 1.1      # kantlengde som utløser deling
STEP_MAX = 0.30  # maks bevegelse per iterasjon i mm
MAX_N = 1500     # nodetak (stopper veksten)
ITERS = 550
SNAP = 70        # tegn snapshot hver N-te iterasjon
R_BOUND = 80     # ytre grense (sirkel) i mm
SEED = 4

CX = CY = R_BOUND + 5
rng = np.random.default_rng(SEED)

ang = np.linspace(0, 2 * np.pi, 50, endpoint=False)
pts = np.stack([CX + 10 * np.cos(ang), CY + 10 * np.sin(ang)], axis=1)
pts += rng.normal(0, 0.3, pts.shape)

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")

for it in range(ITERS):
    diff = pts[:, None, :] - pts[None, :, :]
    dist = np.linalg.norm(diff, axis=2)
    np.fill_diagonal(dist, np.inf)
    naer = dist < R_REP
    w = np.where(naer, (1 - dist / R_REP) / np.maximum(dist, 0.01), 0)
    rep = (diff * w[..., None]).sum(axis=1) * F_REP
    att = ((np.roll(pts, 1, axis=0) + np.roll(pts, -1, axis=0)) / 2 - pts) * F_ATT
    force = rep + att
    norm = np.linalg.norm(force, axis=1, keepdims=True)
    force *= np.minimum(1, STEP_MAX / np.maximum(norm, 1e-9))
    pts += force

    # hold innenfor sirkelgrensen
    rad = np.linalg.norm(pts - [CX, CY], axis=1)
    over = rad > R_BOUND
    if over.any():
        pts[over] = [CX, CY] + (pts[over] - [CX, CY]) * (R_BOUND / rad[over])[:, None]

    # del strukne kanter + sett inn noen tilfeldige noder (selve veksten)
    if len(pts) < MAX_N:
        nxt = np.roll(pts, -1, axis=0)
        elen = np.linalg.norm(nxt - pts, axis=1)
        del_kant = elen > SPLIT
        inject = rng.random(len(pts)) < 0.01  # ~1 % tilfeldig vekst per iterasjon
        nye = []
        for p, m, splitt in zip(pts, (pts + nxt) / 2, del_kant | inject):
            nye.append(p)
            if splitt:
                nye.append(m + rng.normal(0, 0.05, 2))
        pts = np.array(nye[: MAX_N])

    if it % SNAP == 0:
        vsk.polygon(pts, close=True)

vsk.polygon(pts, close=True)

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "differential_growth.svg"))
print(f"Lagret {out / 'differential_growth.svg'} ({len(pts)} noder)")
