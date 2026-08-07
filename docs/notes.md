# Notes — background, alternatives and reference material

Moved out of the README to keep it a pure how-to. Nothing here is needed
for a normal plot.

## CLI (advanced/local use)

[scripts/svg2gcode.py](../scripts/svg2gcode.py) provides the same G-code
flow as the web app for automation and local use. It requires
vpype-flattened SVGs.

```sh
python3 scripts/svg2gcode.py --calibrate
python3 scripts/svg2gcode.py sketches/output/optimized/circle_packing.svg \
  --paper a5 -o sketches/output/gcode/circle_packing.gcode
```

For complex SVGs, [scripts/optimize.sh](../scripts/optimize.sh) merges
and sorts paths (uses `uvx vpype`). Optional before the web app,
required before the CLI.

## Jig design history

- **v1 (L-bracket):** back + right fences only (the datum principle:
  two datum edges lock X, Y and rotation; a left fence would need an
  exact sheet width). The sheet slid under flanges and was taped to the
  plate — which meant taping inside the enclosed cabinet every plot.
- **v2 (window frame, current):** a frame surrounding the sheet on all
  four sides. The window tolerates sheet-width variation via a small
  clearance (`win_clear`), and the sheet is taped to the frame off the
  machine — the enclosed-cabinet ergonomics won over datum purity.
  Registration to the plate is unchanged (right lip + the left part of
  the back lip; the rest of the back edge is cut away to clear the
  rear handle tab and an obstruction behind it not present in Bambu's
  plate STLs).

## Fallback: Orca Slicer

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
   own [`calligraphy/text2svg.py`](../calligraphy/text2svg.py) does this with
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
   [ADR 0001](adr/0001-calligraphy-toolkit-is-paper-agnostic.md)).
   Fonts and their licenses: [calligraphy/fonts/CREDITS.md](../calligraphy/fonts/CREDITS.md).
   Other options: 3dplotter.xyz has 50+ built in; Inkscape has the Hershey
   Text extension; `vpype text` from the command line

   For NN-generated handwriting, pick **Håndskrift — NN** in the web
   app's [text tool](https://mhellevang.github.io/strek/text.html) — the
   Graves RNN runs in the browser (onnxruntime-web, 28 MB lazy-loaded and
   cached) with programmatic `æøå` (attention-placed diacritics,
   auto-resample on skipped letters) and a neatness slider. The CLI
   original is [`calligraphy/nn_text2svg.py`](../calligraphy/nn_text2svg.py);
   it requires
   [pytorch-handwriting-synthesis-toolkit](https://github.com/X-rayLaser/pytorch-handwriting-synthesis-toolkit)
   cloned to `~/git` with a `venv/` (torch 1.x) and the pretrained
   `checkpoints/Epoch_56`; the script re-execs into that venv by itself:

   ```
   python3 calligraphy/nn_text2svg.py "Blåbærsyltetøy på brød" --trials 5
   ```

   Background: [research/nn-handwriting-aeoeaa.md](research/nn-handwriting-aeoeaa.md)
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
  plotters, parameter GUI and seeds. Sketches in [sketches/](../sketches/),
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
  [scripts/optimize.sh](../scripts/optimize.sh) uses `uvx vpype`
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
preserved in [arkiv/4xidraw-design.md](../arkiv/4xidraw-design.md).

## References

- [P2S Pen Plotter Toolhead](https://makerworld.com/en/models/3127692-p2s-pen-plotter-toolhead) — the P2S-specific head mount we use, takes the UMTS pen modules
- [UMTS on MakerWorld](https://makerworld.com/en/models/2029113-modular-system-for-a1-p1-x1-series) — Falu's spring-loaded module system for Bambu printers; the pen modules, calibration numbers and Orca tables come from it
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
- Build references (4xiDraw, FluidNC, DLC32): see [arkiv/4xidraw-design.md](../arkiv/4xidraw-design.md)

## History

- **2026-07-16:** direction set — Bambu P2S as a pen plotter via UMTS,
  focus on calligraphy and generative art. (A DIY plotter build was
  designed and shelved first; the material lives in [arkiv/](../arkiv/),
  and buying an iDraw 2.0 is Plan B)
- **2026-07-17:** 10 vsketch sketches + vpype optimization; our own
  G-code pipeline ([scripts/svg2gcode.py](../scripts/svg2gcode.py))
  replaces the slicer, Orca demoted to fallback; paper jig in
  [jig/](../jig/); renamed to **strek**, translated to English, and the
  [web app](https://mhellevang.github.io/strek/) went live on Pages
