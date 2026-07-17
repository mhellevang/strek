# BOM — deleliste

Mekanikk følger original 4xiDraw-BOM (Instructables) — kryssjekket
2026-07-16 ✓. Elektronikk (7–11) er vårt avvik.
Reell totalsum fra handlekurv 2026-07-16 (ikke bestilt ennå):
**ca. 2600 kr** levert (varer ~$173 + porto $33 + MVA $51 = $256.76,
inkl. penn utenom BOM).
Alt kjøpes på AliExpress — kun fjær/strips/ledning fra skuffen.
Alt fra AliExpress i én bestilling, levering Norge typisk 1–3 uker.

| # | Del | Antall | Ca. pris | Kilde | Status |
|---|---|---|---|---|---|
| 1 | NEMA17 stepper, 42 Ncm, 1.5A, m/1m kabel ([denne](https://www.aliexpress.com/item/1005007354115347.html)) | 2 | 199 kr | AliExpress | ☐ |
| 2 | 8 mm glattstang, herdet: 2× 400 mm (17 kr/stk) + 2× 320 mm (11 kr/stk) ([hihigh Store](https://www.aliexpress.com/item/1005003880308931.html) — har eksakte lengder) | 4 | 57 kr | AliExpress | ☐ |
| 3 | LM8UU lineærlagre, [10-pk](https://www.aliexpress.com/item/1005005041116938.html) | 10 | 10 kr | AliExpress | ☐ |
| 4 | GT2-belte 6 mm åpent, [POWGE 10 m](https://www.aliexpress.com/item/2039635559.html) (behov 1.4 m — resten reserve) | 10 m | 89 kr | AliExpress | ☐ |
| 5 | GT2 pulley 20T, 5 mm boring, for 6 mm belte ([POWGE, velg 5mm + Belt Width 6mm + 2pcs](https://www.aliexpress.com/item/4000564174485.html)) | 2 | 40 kr | AliExpress | ☐ |
| 6 | F623ZZ flenslagre 3×10×4, brukes parvis ([10-pk ABEC-7](https://www.aliexpress.com/item/1005009083923124.html) — velg F623ZZ) | 10 | 107 kr | AliExpress | ☐ |
| 7+8 | MKS DLC32 v2.1 + 3× TMC2209 ("Package 2" i [denne listingen](https://www.aliexpress.com/item/1005003528786927.html)) | 1 pakke | 240 kr | AliExpress | ☐ |
| 9 | SG90 mikroservo, [2-pk **180°**-varianten](https://www.aliexpress.com/item/1005006572297006.html) (ikke 360°!) | 2 (én reserve) | 10 kr | AliExpress | ☐ |
| 10 | 12 V 3 A strømforsyning, 5.5 mm DC-plugg ([f.eks. denne](https://www.aliexpress.com/item/1005009941657114.html) — eller gammel ruterlader/Biltema, tryggere kvalitet) | 1 | 80 kr | AliExpress / lokal | ☐ |
| 11 | Endstop-moduler m/kabel, RAMPS-stil (valgfritt, homing — [3 stk m/kabel](https://www.aliexpress.com/item/1005007576184330.html)) | 3 (2 + reserve) | 31 kr | AliExpress | ☐ |
| 12a | M3 hex-skruesett 90 stk, 4–30 mm SUS304 ([denne](https://www.aliexpress.com/item/32334431524.html) — dekker 8× 30 mm, 8× 6 mm, 4× 16 mm, 2× 15 mm) | 1 | 53 kr | AliExpress | ☐ |
| 12b | M3-muttere + skiver ([denne](https://www.aliexpress.com/item/1005006140198276.html) — velg **M3**-settet, kun den størrelsen trengs) | 1 | 47 kr | AliExpress | ☐ |
| 13a | M10 gjengestang 304, 400 mm ([GLKJ Tools, velg M10x400mm](https://www.aliexpress.com/item/1005002781646885.html), 90 kr/stk) | 2 | 180 kr | AliExpress | ☐ |
| 13b | M10-muttere DIN934 (standard 1.5-gjenging, **ikke** ×1.25 finegjenget) ([10-pk](https://www.aliexpress.com/item/1005004202913032.html)) | 10 | 35 kr | AliExpress | ☐ |
| 14 | Karbonrør OD4/ID3 mm × 500 mm ([denne](https://www.aliexpress.com/item/1005009398012398.html) — kapp 2× 100 mm) | 1 | 70 kr | AliExpress | ☐ |
| 15 | Servo-skjøtekabel 30 cm ([10-pk](https://www.aliexpress.com/item/1005012533117782.html)) | 1 pk | 15 kr | AliExpress | ☐ |
| 16 | Fjær til penneholder, strips, ledning | — | 50 kr | skuffen | ☐ |

## Har allerede

- 3D-printer + filament (PETG anbefalt til braketter)
- ESP32 devkits (ubrukt — DLC32 har innebygd ESP32; devkits kan bli
  reservecontroller om DLC32 ryker)

## Bevisst utelatt

- Arduino Uno + CNC Shield v3 (originalens elektronikk) — erstattet av DLC32
- MGN12-skinner (v1/v3-planene) — printfilene passer originalens
  glattstenger; ingen ferdig MGN12-remix finnes
- Protoboard + A4988 + kondensatorer (v1-planen) — DLC32 har sockets
  og skruterminaler, null lodding
- EBB-kort (~60 USD) — kun ved senere ønske om ekte AxiDraw-programvare
  (Inkscape AxiDraw-extension, Saxi)

## Sjekk ved bestilling

- DLC32: velg **v2.1**, uten TS24/TS35-skjerm — FluidNC støtter ikke
  skjermen ([issue #759](https://github.com/bdring/FluidNC/issues/759)),
  WebUI holder. Kjøp "Package 2" (kort + 3× TMC2209, ~240 kr) — dekker
  linje 7+8 inkl. reservedriver. Unngå Package 1/5/6 (A4988, ikke TMC2209)
- TMC2209: "stepstick"-format (StepStick/BigTreeTech/MKS-modul), ikke
  breakout med skruterminaler
