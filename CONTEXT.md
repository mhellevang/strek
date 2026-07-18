# Context — strek

Glossary for the strek pen-plotting project. Terms only, no implementation.

## Glossary

### Calligraphy toolkit
A standalone CLI script that turns a text string into a **single-stroke SVG**,
ready for the existing pipeline (`optimize.sh` → `svg2gcode.py` / web app).
One input (text + style options), one output (SVG). Not a library, not a GUI
wrapper. Lives alongside the generative-art scripts in `sketches/`.

### Single-stroke SVG
An SVG whose glyphs are centre-line paths — one pen stroke per letter, no
filled contours. This is what a plotter draws directly; distinct from an
outline font (filled shapes) that would need hatching to plot.

### Glyph
The centre-line path(s) for one character plus its horizontal advance,
expressed in a normalised coordinate space. The common currency between
font parsers and the layout engine — parser-agnostic.

### Font (in the toolkit)
A named collection of Glyphs loaded from a source file. Two source formats
are supported, each with its own parser, both producing the same Glyph
model: **EMS SVG fonts** (calligraphic script) and **classic Hershey
`.jhf`** (public-domain engraved/gothic — the "1960s pen" look). Layout and
rendering never know which format a Font came from.

### Layout engine
Places Glyphs into lines to produce the final Single-stroke SVG. Format-
and font-agnostic; consumes only the Glyph model.
