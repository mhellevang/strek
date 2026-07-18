# The calligraphy toolkit sizes in absolute mm and stays paper-agnostic

The `calligraphy/text2svg.py` toolkit specifies text size as an absolute
cap-height in millimetres (`--size`) and emits an SVG whose `width`/`viewBox`
encode that real-world size. It deliberately knows **nothing** about paper,
jig margins, or centering — `scripts/svg2gcode.py` already owns paper size
(`--paper`), places the drawing on the sheet, and bounds-checks it. We chose
this split so each stage has one responsibility (generate correctly-sized
strokes vs. place them on paper) rather than duplicating paper knowledge in
both tools.

A future reader will reasonably ask "why doesn't `text2svg.py` take `--paper`
when `svg2gcode.py` does?" — this is why. The rejected alternative was a
fit-to-paper mode in the toolkit; it was declined because "fill the sheet" is
ambiguous with multi-line text and would fork paper logic across two programs.
A `--paper` *convenience* that merely computes a `--size` may be added later,
but the toolkit's core contract stays absolute-mm and placement-free.
