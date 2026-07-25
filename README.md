# strek — pen plotting and calligraphy

**Main direction (2026-07-17):** plot calligraphy and generative art with
a Bambu Lab P2S acting as a pen plotter via **UMTS** —
[Universal Modular Tool System by Falu](https://makerworld.com/en/models/2029113-modular-system-for-a1-p1-x1-series)
(free, MakerWorld, P2S in the profile list). Zero new parts beyond
printed modules. The **[web app](https://mhellevang.github.io/strek/)**
is the main interface: drop in an SVG, preview the toolpath and download
ready-to-run G-code. It works offline and needs no slicer.
[scripts/svg2gcode.py](scripts/svg2gcode.py) remains available for
command-line use. The Orca setup is a [fallback](#fallback-orca-slicer).
A dedicated plotter is postponed until the hobby has proven itself; if
it happens, the plan is to **buy** (iDraw 2.0), not build — see
[Plan B](#plan-b--dedicated-machine) at the bottom.

## P2S as a plotter (UMTS) — setup

Workflow per plot:

1. Make/get an SVG (sketches in [sketches/](sketches/), the handwriting
   toolkit below, Inkscape, Convertio for image-to-line-art)
2. Open the **[web app](https://mhellevang.github.io/strek/)**, drop in
   the SVG, preview the toolpath and download the `.gcode`
3. Transfer to the printer: microSD, or FTP over LAN
   (`ftps://<printer-ip>`, port 990, user `bblp` + access code from the
   screen). Start from the printer screen — the P2S runs raw `.gcode`
   (confirmed)
4. Put the sheet in the jig, tape the two free corners. The file homes
   first (**without** the pen), parks and pauses (`M400 U1`) — mount the
   pen, press resume. Stay at the machine

For complex SVGs, [scripts/optimize.sh](scripts/optimize.sh) can merge
and sort paths before they are opened in the web app.

### Checklist: first-time setup

- [ ] Print the UMTS modules from the MakerWorld profile (Stabilo module
      for pens, POSCA module for thick markers; a cutter module exists
      too) — regular print jobs with Falu's profiles. Spring-loaded,
      clips onto the printhead, tool change in seconds, ±0.1 mm
- [ ] Print the paper jig ([jig/paper_jig.stl](jig/paper_jig.stl)) —
      an L-bracket that hooks onto the plate's back/right edges and
      gives the margins (29 mm right / 41 mm back) automatically.
      MEASURE `edge_to_bed`/`lip_drop`/the pin positions in the .scad
      file against your plate before printing
- [ ] Masking tape ready — the sheet's two free corners are taped before
      every plot
- [ ] Top glass off, or riser on (spring travel)
- [ ] Calibrate in phases (see [safety rules](#safety-rules-from-the-umts-designer--general)):
  - [ ] Generate a calibration cross in the web app and run it
        **without the pen** — just watch that moves, pauses and
        clearances look right (the nozzle stays 17+ mm above the plate,
        harmless)
  - [ ] Same file with the pen: the cross should sit at the paper's
        center (arrow toward the back wall). Measure the deviation,
        adjust the pen X/Y offsets
  - [ ] Pen pressure: start too high, adjust the pen depth in the module
        or Z draw in 0.1 steps until it draws cleanly and lifts clearly
- [ ] First real plot: BIC/Stabilo in the module AFTER homing, ~0.5 mm
      tip protrusion, stand by the pause button

### Web app

The **[web app](https://mhellevang.github.io/strek/)** ([docs/](docs/) —
also works opened straight from disk, fully offline): drag in one or
more SVGs, preview the toolpath on the bed, tune the parameters and
download `.gcode`. Raw paths, shapes and transforms are flattened by
the browser. Multiple files become pen layers with pauses for swapping
pens.

- Pure pen logic: XY moves along the strokes, 3 mm Z lift between them,
  no E axis — heaters are actively turned OFF (M104/M140 S0). Built-in
  safety: refuses nozzle coordinates outside the legal window
  (X 48–255, Y 55–255), Z floor 16 mm, scales down designs that don't fit
- **Centers on the sheet**, not just in the legal window: choose A4,
  A5 or a custom size and set the pen tip's X/Y offset from the nozzle
  (initially −29/−41 from the jig margins). The preview shows the
  drawing's margins on the sheet
  — on A4 the pen can't reach the bottom ~80 mm; the app shifts the
  drawing and says so
- **Calibrate once:** generate a cross that should sit at the paper's
  center (arrow pointing toward the back wall). Measure the deviation
  and adjust the pen X/Y offsets. Then adjust Z draw (default 17.1) in
  0.1 steps until the pen barely draws. Draw speed defaults to 150 mm/s
  (Stabilo takes 300–400)
- Flow inside the file: `G28` (home **without** pen) → parks near the
  front → `M400 U1` (pause) → mount pen, resume → plots with M73
  progress on the screen → parks at the back
- **Multicolor:** load the SVGs together and the app creates one job
  with pauses between the pen layers. If you run separate G-code files,
  take the pen out before each file because every job starts with G28

#### CLI (advanced/local use)

[scripts/svg2gcode.py](scripts/svg2gcode.py) provides the same G-code
flow for automation and local use. It requires vpype-flattened SVGs.

```sh
python3 scripts/svg2gcode.py --calibrate
python3 scripts/svg2gcode.py sketches/output/optimized/circle_packing.svg \
  --paper a5 -o sketches/output/gcode/circle_packing.gcode
```

### Mechanics

- Stabilo: the tip should protrude ~0.5 mm (barely visible); pressure is
  set by spring + pen depth + Z height
- POSCA: flip the guide + upper spring upside down and tighten the
  screws so the marker's back rests against a fixed reference — constant
  pressure, cleaner lines. POSCA needs `--z-draw` ~20 (module offset
  +20) and low speed (30–40 mm/s)
- **Paper size:** A4 doesn't fit — the plate is 256 mm, A4 is 297. Use
  A5 landscape (210×148, whole sheet drawable) or cut A4 to 210×200
- Flat sheets only — enclosed cabinet

### Paper jig

[jig/paper_jig.scad](jig/paper_jig.scad) is a self-registering L-bracket
that places the sheet at the 29/41 margins automatically — like paper in
a printer tray. It can stay on during plotting (1 mm base, 3 mm pen
lift, 5 mm drawing margin).

```
                back wall
   ╔═▓▓▓▓▓▓▓▓▓▓▓ back arm ▓▓▓▓▓▓▓▓▓▓═╗
   ║  ¦                             ▓║
   ║  ¦left                         ▓║ ← right arm
   ║  ¦mark        SHEET            ▓║
   ║  ¦                             ▓║
   ║               A5 mark ———————— ▓║
   ║ tape↑                          ▓║
   ║               200 mark ------- ▓║
   ║ (the sheet's free corners)     ═╣
   ║                                 ║
   ╚═════════════════════════════════╝
              front (door)              ▓ = lip over the plate edge
```

Use:

1. **Flip it over** — it prints with the lips up; in use the lips point
   down
2. Place it in the plate's **back-right corner**: back arm along the
   back edge, right arm along the right edge. The lips hook down over
   the plate edge — push until it sits snug against both. The locating
   pins at the back go into the notches
3. Feed the sheet in **from the front-left**: push it back and to the
   right until it slides under the 3 mm flanges (0.4 mm air) and butts
   against the inner edges of both arms
4. Check the mark slots: the sheet's left edge lines up with the slot on
   the back arm; the front edge with the solid slot (A5) or the dashed
   one (210×200)
5. Tape the two free corners (front-left and front-right), close the
   door, run — the jig stays on

Only two datum edges is deliberate (the datum principle): back + right
fences lock X, Y and rotation unambiguously. A left fence would require
an exact sheet width — too tight and the sheet buckles, too loose and it
adds slack. The left edge is checked visually against the mark slot
instead.

Before the first print: MEASURE `edge_to_bed`, `lip_drop` and the pin
positions in the .scad file against your plate, and regenerate with
`openscad --export-format binstl -o jig/paper_jig.stl jig/paper_jig.scad`.

### Safety rules (from the UMTS designer + general)

- **Excluded area for the X1/P1/P2 series** (the module occupies physical
  volume; the head can collide with walls/door/glass even where the
  nozzle could reach): `(0x0, 258x0, 258x55, 48x55, 48x258, 0x258)` —
  svg2gcode and the web app enforce this; don't change it without
  understanding the module's real motion limits
- **Paper position is critical** (pen tip ≠ nozzle reference): 29 mm
  margin from the right wall, 41 mm from the back wall — the jig gives
  this automatically
- **The top glass can limit spring travel** — remove it or use a riser
- **Home the machine first, insert the pen after** — the P series
  Z-homes with the nozzle against the plate; a pen mounted during homing
  gives a wrong Z reference
- No heating or extrusion commands in self-generated G-code (no
  M104/M109 with a value, no E moves); never disable soft limits
- Conservative starting Z: begin where the pen barely draws, lower in
  0.1 mm steps. The spring module is the mechanical fuse — the worst
  outcome is a ruined pen tip, not a ruined printer
- **Calibrate in phases** (from the rebelthor repo): 1) generate the
  files, 2) run with only the base mount (verify the pauses), 3) full
  module without pen (clearance), 4) pen — start too high, pause, push
  the pen 1–2 mm deeper into the module, resume; repeat until it draws
  cleanly and lifts clearly. No regeneration — the pen depth is the
  adjustment
- Dry-run the first file without a pen and watch; stay at the machine
  for the first real runs
- At the end-of-plot pause: the file parks at the back and pauses — take
  the pen out BEFORE doing anything else with the machine

### Fallback: Orca Slicer

Documented working by the UMTS designer (and verified for the P1S in
[rebelthor/bambu-lab-pen-plotter](https://github.com/rebelthor/bambu-lab-pen-plotter)).
The core trick: the slicer is fooled into thinking it's printing —
extrusion is nulled out via the filament profile, Z-hop becomes the pen
lift. Use this route if svg2gcode files turn out not to run.

Setup (once): Orca Slicer in **LAN-only mode** (Bambu Studio doesn't
handle the Z compensation). Copy the P2S preset → "P2S plotter", paste
the start G-code from the rebelthor repo (replace everything — the stock
code has G29 leveling and a purge line that must NOT run with a pen),
prepend the safe finish to the end G-code (lift 20 mm + `M400 U1`
"remove pen" BEFORE the stock end), and enter the values below.

**Machine (Printer Settings → Machine):**

| Setting | Value | Why |
|---|---|---|
| Z offset | **+17.0 mm** (Stabilo) / **+20.0 mm** (POSCA) | The pen hangs below the nozzle |
| Excluded area | `(0x0, 258x0, 258x55, 48x55, 48x258, 0x258)` | The module occupies volume — collision guard |

**Filament profile "plotter mode" (mandatory — the firmware refuses to
run entirely without an extruder):**

| Setting | Value | Why |
|---|---|---|
| Nozzle temp | 180 °C | Avoids the "cold extrusion prevention" error |
| Bed temp | 25 °C (lowest possible) | Avoids paper deformation |
| Flow ratio | **0.01** | The extruder effectively pushes nothing |
| Max volumetric speed | 22 mm³/s | |
| All fans (part/aux/chamber) | **0 %** | Vibration + airflow moves the paper, gives wavy lines |

**Process profile (drawing module):**

| Setting | Value |
|---|---|
| Layer height / first layer | 0.10 mm |
| All line widths | 0.40 mm (= Stabilo tip) |
| Perimeters | 1 |
| Retraction | **0.01 mm** (only to unlock the Z-hop field) |
| Z-hop | **3 mm**, 90°/Normal — this is the pen lift; without it = ink ghosting |
| Closing radius / resolution | 0.001 / 0.012 |
| XY hole/contour compensation | −0.075 / +0.075 |
| Speed | 300–400 mm/s (Stabilo), 30–40 mm/s (POSCA) |
| Infill | Rectilinear aligned, only if filled areas are wanted |

The sketches' working width is deliberately 210 mm (= A4): "Center" in
the slicer then centers physically on the sheet with no offset fiddling.

## Calligraphy from text

Regular fonts are outline fonts (filled contours); a plotter draws
strokes. Three techniques, happily combined:

1. **Single-stroke fonts (Hershey)** — every letter is one pen path. Our
   own [`calligraphy/text2svg.py`](calligraphy/text2svg.py) does this with
   no Inkscape: text in → single-stroke SVG out, ready for the pipeline.
   Ships with EMS fonts (script: Allure, Delight, Casual Hand, Brush;
   sans: Readability, Nixish) and classic Hershey in sans, serif, script
   and gothic (the 1960s-pen look) — all 13 with full `æøå` coverage:

   ```
   python3 calligraphy/text2svg.py "Hei Strek" --font EMSAllure --size 14
   python3 calligraphy/text2svg.py dikt.txt --font HersheyScript1 -o dikt.svg
   python3 calligraphy/text2svg.py --list-fonts
   ```

   The fonts are stored as coarse polylines, so a Chaikin `--smooth`
   pass (default 2) rounds them into flowing script; use `--smooth 0` to
   keep the sharp corners of `HersheyGothEnglish`. `--size` is the cap-height in mm;
   the toolkit stays paper-agnostic and lets `svg2gcode.py` place the text
   (see
   [ADR 0001](docs/adr/0001-calligraphy-toolkit-is-paper-agnostic.md)).
   Fonts and their licenses: [calligraphy/fonts/CREDITS.md](calligraphy/fonts/CREDITS.md).
   Other options: 3dplotter.xyz has 50+ built in; Inkscape has the Hershey
   Text extension; `vpype text` from the command line
2. **The pen does the calligraphy** — broad-edge calligraphy IS a pen at
   a constant angle where stroke width varies with direction, and a
   plotter holds the angle perfectly. Pilot Parallel + a simple script
   font = thick/thin for free, and authentic. The most underrated move
3. **Outline font + hatch fill** — text to path in Inkscape, fill the
   outline with hatching (the Hatch fill extension or vpype). Slower,
   gives calligraphic weight with a regular fineliner

Bonus levels:

- [calligrapher.ai](https://www.calligrapher.ai) — a neural net that
  generates realistic handwriting (every letter unique), exports SVG
- Your own handwriting: write on an iPad/drawing tablet, export the
  strokes as SVG
- Advanced: brush pen + Z modulation along the way for pressure
  variation (possible since Z is controllable in our own G-code, an
  advanced exercise)

## Generative art

Plotter art = single strokes, no filled areas — hatching replaces fill.
Genres to explore:

**Algorithmic from scratch:**

- **Flow fields** — perlin noise steers thousands of curves; the most
  popular plotter genre, easy to start, endless variation
- **"Joy Division" landscapes** — horizontal noise lines with occlusion;
  beginner-friendly, looks good fast
- **Truchet tiles** — a grid of rotated tile patterns (arcs/diagonals)
- **L-systems / fractals** — plants, Hilbert curves, dragon curves
- **Differential growth** — organic, coral-like lines that grow and
  repel each other
- **Circle packing, voronoi, delaunay** — geometric fill
- **Harmonograph / spirograph** — parametric curves, very little code
- **Mazes and space-filling curves**

**From photos:**

- **TSP art / stippling** — a photo becomes one continuous stroke
  (StippleGen)
- **Hatching portraits** — DrawingBotV3 converts images to plotter
  paths, zero coding

**Tools:**

- [vsketch](https://github.com/abey79/vsketch) (Python) — made for
  plotters, parameter GUI and seeds. Sketches in [sketches/](sketches/),
  run with `uv run --with vsketch python sketches/<name>.py`:

  | Sketch | Genre | Pens |
  |---|---|---|
  | `joy_division.py` | Noise landscape with occlusion | 1 |
  | `flow_field.py` | Perlin angle field, 600 strokes | 3 (quantile-balanced) |
  | `truchet.py` | Quarter-circle tiles, meander pattern | 2 (one per variant) |
  | `lsystem_plant.py` | Fractal plant, turtle interpretation | 1 |
  | `hilbert.py` | Space-filling curve — one stroke, zero pen lifts | 1 |
  | `labyrint.py` | Recursive backtracker, entrance/exit | 1 |
  | `circle_packing.py` | Grow-until-collision | 3 (by size) |
  | `voronoi.py` | Noise-driven density, deduplicated edges | 1 |
  | `harmonograph.py` | Damped Lissajous pendulums | 1 |
  | `differential_growth.py` | Organic curve growth with snapshots | 1 |
- [vpype](https://github.com/abey79/vpype) — post-processing: merge
  lines, sort paths, cuts plot time drastically.
  [scripts/optimize.sh](scripts/optimize.sh) uses `uvx vpype`
  automatically. It is optional before the web app and required before
  the CLI
- [DrawingBotV3](https://drawingbotv3.com) /
  [StippleGen](https://wiki.evilmadscientist.com/StippleGen) — GUI,
  zero code
- p5.js + p5.plotSvg — the JS alternative

### Multicolor with DrawingBotV3 (e.g. 6× Stabilo Point 88)

1. **Pen set**: the Pens tab has a Stabilo Point 88 preset — duplicate
   and delete the colors you don't have. Tip: scan real strokes on your
   paper and eyedrop from that; on-screen ink colors lie
2. **PFM**: "Sketch Lines"/"Sketch Curves" with **Colour Match** enabled
   — each stroke is assigned the pen closest to the image underneath.
   Without Colour Match everything is drawn with one pen regardless of
   set size (the most common mistake). The CMYK PFMs want C/M/Y/K pens,
   they don't fit arbitrary sets
3. **Per pen**: stroke width 0.4 mm (Point 88), distribution weight if
   one color dominates, opacity ~0.8 in the preview simulates marker
   overlap
4. **Export**: File → **Export per/pen** → SVG, one file per color. Open
   all files together in the web app
5. **Plotting**: run the combined G-code and swap pens at each pause
   without moving the paper. Order the files light → dark — dark strokes
   hide registration errors

## Pens

Order to master:

1. **Gel pen/fineliner** (uni-ball ZENTO, Sakura Pigma) — easiest,
   fault-tolerant, start here
2. **Pilot Parallel** (2.4 mm is a good start) — a broad-edge fountain
   pen made for constant angle and zero pressure; the calligraphy
   workhorse
3. **Regular fountain pen** — gorgeous wet line, but: the nib is
   designed for a ~45–55° angle (a vertical holder can skip — an angled
   holder remix helps), needs almost zero spring pressure (too stiff a
   spring splays the tines), and ink flow doesn't always keep up at
   plotter speed — lower the speed (`--draw-speed`)

Paper decides with liquid ink: Rhodia/Clairefontaine class, otherwise
the line feathers.

## Plan B — dedicated machine

If P2S plotting sticks and the 256×256/flat-sheet limitation starts to
hurt: **buy a UUNA TEK iDraw 2.0 A4** (~4650 NOK new at
idrawpenplotter.com; open-box $299 at uunatek.com when in stock — a
steal). Best ready-made machine under NextDraw money. The SVG pipeline
(sketches → vpype) is reused as-is; only the G-code dialect changes.

A self-build (the 4xiDraw clone) was shelved on 2026-07-17 — buying
gives more plotting per hour of free time. All the build material
(verified BOM, build guide, FluidNC config, design decisions) is
preserved in [arkiv/4xidraw-design.md](arkiv/4xidraw-design.md).

## References

- [UMTS on MakerWorld](https://makerworld.com/en/models/2029113-modular-system-for-a1-p1-x1-series) — module system for Bambu printers, free (main direction)
- [rebelthor/bambu-lab-pen-plotter](https://github.com/rebelthor/bambu-lab-pen-plotter) —
  clean rewrite of the UMTS setup for the P1S: verified profiles,
  start/end G-code, phased calibration. The numbers match the tables
  above
- [3dplotter.xyz](https://3dplotter.xyz) — web app + pen holder STLs
  (alternative with nicer text tools; P2S support in their pipeline as
  of July 2026)
- [vpype](https://github.com/abey79/vpype) — SVG optimization, the
  workhorse in `optimize.sh`
- [calligrapher.ai](https://www.calligrapher.ai) — generated handwriting
  as SVG. Locally:
  [pytorch-handwriting-synthesis-toolkit](https://github.com/X-rayLaser/pytorch-handwriting-synthesis-toolkit)
  (modern, CLI, recommended),
  [sjvasquez/handwriting-synthesis](https://github.com/sjvasquez/handwriting-synthesis)
  (the original code, TF 1.x),
  [GirkovArpa/calligrapher-ai](https://github.com/girkovarpa/calligrapher-ai)
  (offline desktop app)
- [awesome-plotters](https://github.com/beardicus/awesome-plotters) — ecosystem overview
- Bantam Tools NextDraw 8511 — commercial reference (~675 USD)
- Build references (4xiDraw, FluidNC, DLC32): see [arkiv/4xidraw-design.md](arkiv/4xidraw-design.md)

## History

- **2026-07-16:** direction set — Bambu P2S as a pen plotter via UMTS,
  focus on calligraphy and generative art. (A DIY plotter build was
  designed and shelved first; the material lives in [arkiv/](arkiv/),
  and buying an iDraw 2.0 is Plan B)
- **2026-07-17:** 10 vsketch sketches + vpype optimization; our own
  G-code pipeline ([scripts/svg2gcode.py](scripts/svg2gcode.py))
  replaces the slicer, Orca demoted to fallback; paper jig in
  [jig/](jig/); renamed to **strek**, translated to English, and the
  [web app](https://mhellevang.github.io/strek/) went live on Pages
