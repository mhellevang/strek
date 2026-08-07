# strek

Pen plotting with a Bambu Lab P2S 3D printer. The pen sits in a
[UMTS](https://makerworld.com/en/models/2029113-modular-system-for-a1-p1-x1-series)
pen module (Universal Modular Tool System by Falu) on the
[P2S Pen Plotter Toolhead](https://makerworld.com/en/models/3127692-p2s-pen-plotter-toolhead)
mount — free, printable, clips onto the printhead; no printer
modifications. The flow is SVG →
[web app](https://mhellevang.github.io/strek/) → `.gcode` → the printer
draws it. No slicer involved.

This README is the how-to: [pen holder](#1-print-and-mount-the-pen-holder) →
[paper](#2-place-the-paper-jig-or-tape) → [G-code](#3-generate-transfer-and-run-the-g-code).
Everything else (calligraphy toolkit, generative art, Orca fallback,
pen guide, references, history) lives in [docs/notes.md](docs/notes.md).

## What's in this repo

| Directory | What |
|---|---|
| [docs/](docs/) | The web app ([live on Pages](https://mhellevang.github.io/strek/)) — drop in SVGs, preview the toolpath, download G-code. Works opened straight from disk |
| [calligraphy/](calligraphy/) | `text2svg.py` — text → single-stroke SVG, 13 Hershey/EMS fonts with full `æøå` |
| [sketches/](sketches/) | 10 generative-art sketches (flow fields, truchet, hilbert, …) for [vsketch](https://github.com/abey79/vsketch) |
| [scripts/](scripts/) | `svg2gcode.py` (CLI version of the web app's G-code pipeline), `optimize.sh` (vpype path merge/sort) |
| [jig/](jig/) | Self-registering paper jig, OpenSCAD + STL |
| [arkiv/](arkiv/) | A shelved DIY-plotter build, kept for reference |

## 1. Print and mount the pen holder

1. Print the
   [P2S Pen Plotter Toolhead](https://makerworld.com/en/models/3127692-p2s-pen-plotter-toolhead)
   mount and the pen module from
   [UMTS](https://makerworld.com/en/models/2029113-modular-system-for-a1-p1-x1-series)
   (Stabilo module for pens) — regular print jobs with the models'
   profiles
2. The mount clips onto the printhead; the spring-loaded pen module
   clips into the mount — no printer modifications
3. **Pen in the module:** slide the pen down through the spring stack
   and guide until the tip protrudes ~0.5 mm (barely visible), then
   clamp it with the small screw in the top spring block. Tightening
   can push the pen slightly down — leave a hair of clearance first
4. Take the top glass off, or use a riser — the spring needs travel
5. **Always home first, mount the pen after** — the P series Z-homes
   with the nozzle against the plate; a pen mounted during homing gives
   a wrong Z reference. The G-code files pause for this automatically

## 2. Place the paper (jig or tape)

The pen tip is offset from the nozzle, so paper position is critical:
**29 mm from the right wall, 41 mm from the back wall.** A4 doesn't fit
(plate is 256 mm) — use A5 landscape (210×148) or cut A4 to 210×200.
Flat sheets only.

### With the jig (recommended)

[jig/paper_jig.scad](jig/paper_jig.scad) is a window frame that
surrounds the sheet on all four sides and registers against the plate's
back and right edges — the window places the sheet at the 29/41 margins
automatically. The sheet is taped to the frame **off the machine**; the
frame stays on during plotting.

Before printing it: MEASURE `edge_to_bed` and `lip_drop` in the .scad
file against your plate. The window is sized by `paper_w`/`paper_h`
(default A5 landscape 210×148; set 210×200 for cut A4 — one frame per
format). Regenerate with
`openscad --export-format binstl -o jig/paper_jig.stl jig/paper_jig.scad`
and print [jig/paper_jig.stl](jig/paper_jig.stl).

```
                back wall
   ╔═▓▓▓▓▓▓▓═════════════════════════╗
   ║ ┌───────────────────────────┐  ▓║
   ║ │                           │  ▓║ ← right lip
   ║ │      SHEET (window)       │  ▓║
   ║ │  tape the corners to      │  ▓║
   ║ │  the frame                │  ▓║
   ║ └───────────────────────────┘  ═╣
   ╚══════════════════════════════════╝
              front (door)              ▓ = lip over the plate edge
```

1. **Flip it over** — it prints with the lips up; in use the lips point
   down
2. **On a table:** drop the sheet into the window (it lies flush on the
   table inside the frame) and tape all four corners to the frame top
3. Carry it to the printer and place it in the plate's **back-right
   corner**: the lips hook down over the back/right plate edges — push
   until it sits snug against both. The back lip only covers the left
   part of the back edge; the rest is cut away to clear the plate's
   rear handle tab and the machine's parts behind it
4. Close the door, run — the jig stays on. Swap sheets by lifting the
   whole frame out

### Without the jig (manual tape)

Measure from the plate edges: the sheet's right edge 29 mm from the
right wall, its back edge 41 mm from the back wall, square to the
edges. Tape all four corners. Same margins every time — the G-code
assumes them.

## 3. Generate, transfer and run the G-code

1. Make/get an SVG ([sketches/](sketches/), the calligraphy toolkit —
   see [docs/notes.md](docs/notes.md) — Inkscape, or Convertio for
   image-to-line-art)
2. Open the **[web app](https://mhellevang.github.io/strek/)** (also
   works opened straight from disk), drop in the SVG, preview the
   toolpath and download the `.gcode`. Choose A5 or custom paper size;
   the preview shows the drawing's margins on the sheet
3. Transfer to the printer: microSD, or FTP over LAN
   (`ftps://<printer-ip>`, port 990, user `bblp` + access code from the
   printer screen). Start the file from the printer screen — the P2S
   runs raw `.gcode`
4. The file homes first (**without** the pen), parks near the front and
   pauses (`M400 U1`) — mount the pen, press resume. It plots with
   progress on the screen, then parks at the back and pauses — **take
   the pen out before doing anything else** (every job starts with G28)
5. **Multicolor:** load the SVGs together in the web app — one job with
   a pause between pen layers; swap pens without moving the paper

The G-code is pure pen logic: XY moves, 3 mm Z lift between strokes,
heaters off, and it refuses coordinates outside the legal window
(X 48–255, Y 55–255, Z floor 16 mm).

### First-time calibration

1. Generate a calibration cross in the web app and run it **without
   the pen** — just watch that moves, pauses and clearances look right
   (the nozzle stays 17+ mm above the plate, harmless)
2. Same file with the pen: the cross should sit at the paper's center
   (arrow toward the back wall). Measure the deviation, adjust the pen
   X/Y offsets in the web app (initially −29/−41 from the jig margins)
3. Pen pressure: start too high; pause, loosen the screw and push the
   pen 1–2 mm deeper into the module, resume — repeat until it draws
   cleanly and lifts clearly.
   Fine-tune with Z draw (default 17.1) in 0.1 steps. Draw speed
   defaults to 150 mm/s (Stabilo takes 300–400)
4. Stay at the machine for the first real runs

### Safety rules

- **Excluded area** `(0x0, 258x0, 258x55, 48x55, 48x258, 0x258)` — the
  holder occupies physical volume; the head can collide with
  walls/door/glass even where the nozzle could reach. The web app and
  svg2gcode enforce this; don't change it
- No heating or extrusion commands in self-generated G-code (no
  M104/M109 with a value, no E moves); never disable soft limits
- Conservative starting Z: begin where the pen barely draws, lower in
  0.1 mm steps. The spring module is the mechanical fuse — the worst
  outcome is a ruined pen tip, not a ruined printer
