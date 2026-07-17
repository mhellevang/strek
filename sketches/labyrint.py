"""Labyrint: recursive backtracker på rutenett.

Perfekt labyrint (én unik vei mellom alle par). Inngang oppe til
venstre, utgang nede til høyre.

Kjør:  uv run --with vsketch python sketches/labyrint.py
Ut:    sketches/output/labyrint.svg
"""

import pathlib

import numpy as np
import vsketch

COLS, ROWS = 30, 42
CELL = 5.5  # mm
SEED = 3

rng = np.random.default_rng(SEED)

# grav ganger: carved = par av naboceller uten vegg mellom
carved = set()
visited = {(0, 0)}
stack = [(0, 0)]
while stack:
    c = stack[-1]
    naboer = [
        n
        for n in [(c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)]
        if 0 <= n[0] < COLS and 0 <= n[1] < ROWS and n not in visited
    ]
    if naboer:
        n = naboer[rng.integers(len(naboer))]
        carved.add(frozenset((c, n)))
        visited.add(n)
        stack.append(n)
    else:
        stack.pop()

vsk = vsketch.Vsketch()
vsk.size("a4", landscape=False, center=True)
vsk.scale("mm")

W, H = COLS * CELL, ROWS * CELL
vsk.line(CELL, 0, W, 0)      # toppkant, hull i celle (0,0) = inngang
vsk.line(0, H, W - CELL, H)  # bunnkant, hull i siste celle = utgang
vsk.line(0, 0, 0, H)
vsk.line(W, 0, W, H)

for i in range(COLS):
    for j in range(ROWS):
        # høyre vegg
        if i < COLS - 1 and frozenset(((i, j), (i + 1, j))) not in carved:
            vsk.line((i + 1) * CELL, j * CELL, (i + 1) * CELL, (j + 1) * CELL)
        # bunnvegg
        if j < ROWS - 1 and frozenset(((i, j), (i, j + 1))) not in carved:
            vsk.line(i * CELL, (j + 1) * CELL, (i + 1) * CELL, (j + 1) * CELL)

out = pathlib.Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
vsk.save(str(out / "labyrint.svg"))
print(f"Lagret {out / 'labyrint.svg'}")
