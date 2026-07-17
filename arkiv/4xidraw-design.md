# Arkivert: 4xiDraw-klonen (eget bygg)

**Status 2026-07-17: skrinlagt.** P2S + UMTS dekker behovet; blir det
aktuelt med dedikert maskin igjen, er kjøp (UUNA TEK iDraw 2.0) mer
realistisk enn bygg i småbarnsfasen. Alt her bevart for referanse —
delelisten var ferdig verifisert og AliExpress-kurven klar, ubestilt.

- Deleliste: [BOM.md](BOM.md) (~2600 kr levert)
- Byggetrinn: [BYGGEGUIDE.md](BYGGEGUIDE.md)
- FluidNC-konfig: [fluidnc/config.yaml](fluidnc/config.yaml)

## Konsept

XY-penneplotter med A4-tegneområde: original 4xiDraw-mekanikk (misan),
uendret — kun elektronikken modernisert (MKS DLC32 + TMC2209 + FluidNC).
Cantilever-form som originalen: åpen front, maskinen kan stå oppå/ved
siden av arbeidsstykket — plotter i notatbøker, på kort, på ark større
enn maskinen.

## Designvalg

| Valg | Beslutning | Hvorfor |
|---|---|---|
| Geometri | 4xiDraw cantilever, A4 | Cantilever-flex biter først ved A3+; NextDraw 8511 selv er A4 cantilever. CoreXY (PlotteRXY) vurdert og forkastet som overkill |
| Føringer | 8mm glattstenger + LM8UU, som originalen | Printfilene passer uendret — ingen remix-jakt. iDraw 2.0 (kommersielt produkt) bruker samme løsning i A4. MGN12 vurdert, forkastet: ingen ferdig remix finnes, egendesign = prosjekt foran prosjektet |
| Controller | MKS DLC32 v2.1 (~180 kr) | ESP32-basert, laget for laser/plotter: driversockets, skruterminaler, endstop-pinner, 12–24 V. Offisiell FluidNC-konfig finnes. Valgt over løse ESP32-devkits (slipper protoboard-lodding) og FYSETC E4 (loddede drivere, servo-uvennlig pinout) |
| Drivere | 2× TMC2209 stepsticks i socket | Stillegående (StealthChop), jevnere mikrostepping enn A4988. Socket = byttbar ved havari |
| Firmware | FluidNC | YAML-konfig uten rekompilering, WiFi + WebUI for G-code-opplasting, RC-servo som Z-akse |
| Penneløft | SG90-servo som Z-akse | Standard `Z`-moves i G-code, funker rett fra vpype/gcodetools |
| Verktøykjede | Inkscape / vpype → G-code → FluidNC WebUI | Ikke EBB/AxiDraw-økosystemet (inkompatibel protokoll). EBB-kort (~60 USD) kan ettermonteres om AxiDraw-programvare ønskes senere |

## Byggeplan

1. Bestill deler fra AliExpress (se [BOM.md](BOM.md)) — lengst ledetid,
   bestill først
2. Mens deler er underveis: print 3D-deler rett fra
   [Thingiverse thing:1444216](https://www.thingiverse.com/thing:1444216),
   ingen modifikasjoner. PETG foretrukket (PLA kryper under beltestrekk),
   6+ perimeters på belastede deler
3. Flash DLC32 med FluidNC via <https://installer.fluidnc.com> (Chrome),
   last opp [fluidnc/config.yaml](fluidnc/config.yaml) via WebUI.
   NB: ta backup av MKS-firmwaren først om du vil kunne gå tilbake
4. Elektronikk: TMC2209-stepsticks i X/Y-socket (riktig vei! sjekk
   silketrykk), motorer og PSU i skruterminaler. Servo: signal på
   gpio.32 (TTL/laser-headeren), 5 V fra ekspansjonsheader
5. Ramme og aksler per 4xiDraw-guiden — omformattert i
   [BYGGEGUIDE.md](BYGGEGUIDE.md). LM8UU-lagre skal
   gli uten slark — mål stengene, kinesiske 8mm-stenger varierer.
   Hold Y-armen kort — A4-rekkevidde, ikke mer (flex)
6. Belterigging: mixed-axis som original 4xiDraw — begge motorer
   stasjonære, ett langt GT2-belte i H-mønster. Følg 4xiDraw-diagrammet
   nøye, lett å rigge speilvendt. Stram til beltet "plinger", ikke mer
7. Kalibrer steps/mm: teoretisk 80 (20T GT2, 1/16 microstepping), men
   TMC2209 i standalone-modus kan stå på annen microstepping avhengig av
   MS-pinner — **mål faktisk bevegelse** (be om 100 mm, mål, juster
   `$100`/`$101` forholdsmessig)
8. Servo + fjærbelastet penneholder til slutt — viktigste enkeltdel for
   strekkvalitet

## Kjente feller

- DLC32 bruker I2S-skiftregister for step/dir (I2SO-pinner i konfigen) —
  begrenser maks steprate noe, irrelevant for plotterhastigheter.
  Servo MÅ derimot på ekte GPIO (gpio.32), I2SO kan ikke lage servo-PWM
- Bevegelse diagonal ved jog-test? Belteriggingen er H-bot — endre
  `kinematics:` fra `Cartesian:` til `CoreXY:` i konfigen (4xiDraw-rigging
  er kartesisk mappet, men remixer varierer)
- Speilvendt akse: bytt `direction_pin`-polaritet i konfig (`:low`/`:high`),
  ikke lodd om motorkontakt

## Referanser

- [4xiDraw på Instructables](https://www.instructables.com/4xiDraw/) — originaldesign og beltediagram
- [FluidNC MKS DLC32-side](http://wiki.fluidnc.com/en/hardware/3rd-party/MKS_DLC32)
- [Offisiell DLC32 v2.1 FluidNC-konfig](https://github.com/bdring/fluidnc-config-files/blob/main/official/MKS_DLC32_v21_laser.yaml) — pinnefasit
- [V1E-forumtråd: DLC32 pen plotter H-bot](https://forum.v1e.com/t/configure-mks-dlc32-for-pen-plotter-hbot/38434)
