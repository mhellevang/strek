# Font credits & licensing

Fonts vendored for the strek calligraphy toolkit (`calligraphy/text2svg.py`).

## Hershey (`hershey/*.jhf`) — Public domain

Classic single-stroke vector fonts by Dr. Allen V. Hershey (US Naval Weapons
Laboratory, 1967). Public domain. `.jhf` files via the
[kamalmostafa/hershey-fonts](https://github.com/kamalmostafa/hershey-fonts)
distribution.

- Script/kalligrafi: `cursive.jhf`, `scripts.jhf`, `gothiceng.jhf`
- Sans-serif: `futural.jhf` (enkeltstrøk), `futuram.jhf` (dobbeltstrøk), `rowmans.jhf`
- Serif: `timesr.jhf`, `timesrb.jhf` (halvfet)

Hershey fonts are ASCII-only — no `æ ø å`. For Norwegian text use an EMS font
(all six cover `æ ø å Æ Ø Å`).

## EMS (`ems/*.svg`) — SIL Open Font License 1.1

SVG single-stroke fonts curated and SVG-converted by
Windell H. Oskay (Evil Mad Scientist / Bantam Tools), created by
Sheldon B. Michaels, from the [oskay/svg-fonts](https://gitlab.com/oskay/svg-fonts)
distribution. Licensed under the SIL Open Font License 1.1 — full text in
[`ems/OFL.txt`](ems/OFL.txt). Each is a single-stroke derivative of a Google
Fonts family:

| File | Font | Derivative of | Original designer |
|------|------|---------------|-------------------|
| `EMSAllure.svg`     | EMS Allure      | Allura              | Rob Leuschke, TypeSETit |
| `EMSBrush.svg`      | EMS Brush       | Alex Brush          | Rob Leuschke, TypeSETit |
| `EMSCasualHand.svg` | EMS Casual Hand | Covered By Your Grace | Kimberly Geswein |
| `EMSDelight.svg`    | EMS Delight     | Delius              | Natalia Raices |
| `EMSNixish.svg`     | EMS Nixish      | Nixie One           | Jovanny Lemonad |
| `EMSReadability.svg` | EMS Readability | Source Sans Pro Light | Paul D. Hunt, Adobe |

The OFL permits bundling and redistribution; the fonts keep their Reserved
Font Names and are not sold on their own. Full per-font metadata (author,
source link) lives inside each `.svg`.
