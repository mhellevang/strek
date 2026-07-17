# Byggeguide — mekanisk montering (4xiDraw)

Omformattert fra [4xiDraw på Instructables](https://www.instructables.com/4xiDraw/)
(misan). Mekanikken (steg 1–2) følges eksakt. Originalens elektronikk- og
programvaresteg (3–5) er **erstattet** av vårt oppsett — se
[Elektronikk og firmware](#elektronikk-og-firmware-vårt-avvik) nederst
og [README.md](README.md).

Nyttig underveis: originalen har en
[interaktiv 3D-modell på Onshape](https://www.thingiverse.com/thing:1444216)
(lenket fra Thingiverse) med explode-visning — bruk den når det er uklart
hvordan deler griper i hverandre.

## Deler

Full deleliste med lenker og status: [BOM.md](BOM.md).

Originalens krav verdt å merke seg:

- **Steppermotorer maks 40 mm høye** — ellers trengs de alternative
  "taller parts"-printdelene for 48 mm-motorer
- GT2-belte: 1,4 m behov
- Servokabelen på SG90 er for kort — 250 mm skjøtekabel nødvendig (BOM #15)

3D-deler: print rett fra [Thingiverse thing:1444216](https://www.thingiverse.com/thing:1444216),
ingen modifikasjoner. PETG, 6+ perimeters på belastede deler.

## Mekanisk montering

### Fase 1 — basen (X-akse)

1. Tre **2× LM8UU** inn på hver av de to **lengste** glattstengene (400 mm)
2. Skyv stengene inn i de to motorholder-delene, én på hver side.
   **La stengene stikke 20 mm ut** på den ene siden, mot motoren —
   dette bærer controllerholderen senere
3. Sett inn de to **M10-gjengestengene** slik at hver støtter én side av
   motorholderne, låst med én mutter på hver side (totalt 8 M10-muttere)
4. Monter de to **NEMA17-motorene** på de store plastdelene med
   8× M3-skruer (originalen sier 8 mm; vårt skruesett dekker med 6 mm)

### Fase 2 — vognen (X møter Y)

5. Press **8× M3-muttere** inn i mutterlommene i den nederste, firkantede
   vognen, og legg vognen på LM8UU-lagrene på de lange stengene
6. Tre **2× LM8UU** inn på hver av de to **korteste** glattstengene (320 mm)
7. Sett en **endY-del** på hver ende av stangparet — Y-aksen er nå ferdig
8. Legg den øverste firkantede vognen over de 4 lagrene på de korte stengene
9. Stikk **4× M3 30 mm** inn i de 4 midterste hullene i toppvognen.
   Snu vognen forsiktig opp-ned så skruehodene hviler på bordet og
   skruene peker opp
10. På hver av de fire skruene: tre på **ett F623ZZ-lager med flensen ned**,
    så en **M3-skive**, så **ett F623ZZ-lager med flensen opp**
11. **Post-it-trikset:** press en post-it-lapp ned over de fire skruespissene
    så papiret perforeres og ligger an mot lagrene — holder dem på plass
    når du snur det hele
12. Legg toppvognen over bunnvognen slik at de korte stengene står
    **vinkelrett** på de lange
13. Skru de fire M3-skruene lett til; når hver har fått tak i mutteren under,
    riv bort post-it-lappen. Trekk til, og sett inn de **4 resterende
    M3 30 mm** (uten lagre — de bare styrker sammenføyningen)

### Fase 3 — belte

14. Sett en **GT2-pulley 20T** på hver motoraksel — **ikke** trekk til
    settskruen ennå
15. På endY-delen som skal bære servoen: monter **et par F623ZZ med
    M3-skive imellom**, festet med en M3-skrue (dette er belteidleren)
16. Tre beltet langs hele banen — **kryssingene i midtvognen er fikse
    greier**, følg beltediagrammet i originalen nøye (lett å rigge
    speilvendt). Når pulleyene er justert i flukt med beltet, trekk til
    settskruene
17. Stram til beltet «plinger» ved knips, ikke mer (fra README)

### Fase 4 — penneløfter

18. Fest servoholder-delen med 2× M3-skruer og muttere, monter deretter
    **SG90-servoen** med de to skruene som følger med den
19. Sjekk at de to vertikale hullene i servoholderen er **4 mm** og at
    karbonrørene glir inn (bor opp med 4 mm-bor om ikke). Stikk begge
    rørene inn ovenfra, men bare **halvveis**. Sett så den vertikale
    vognen («smilefjes»-delen) på ovenfra, press den forsiktig ned til
    du får skjøvet resten av karbonrørene inn i de nederste hullene
20. Fest penneholder-delen til den vertikale vognen med 2× M3-skruer
    og muttere

### Fase 5 — controllerholder

21. Press controllerholderen inn på de utstikkende glattstengene ved den
    ene motorholderen (de 20 mm fra punkt 2). Originaldelen er tegnet
    for Arduino UNO — DLC32 har annet hullbilde, så påregn remix eller
    egen adapterplate

Mekanisk montering ferdig.

### Sjekkpunkter (fra README)

- LM8UU skal gli **uten slark** — mål stengene, kinesiske 8 mm-stenger
  varierer
- Hold Y-armen kort — A4-rekkevidde, ikke mer (cantilever-flex)

## Elektronikk og firmware (vårt avvik)

Originalens steg 3–5 (GRBL på Arduino UNO + CNCShield + Universal Gcode
Sender) gjelder **ikke** dette bygget — erstattet av MKS DLC32 + TMC2209 +
FluidNC. Se [README.md](README.md) punkt 3–4 og
[fluidnc/config.yaml](fluidnc/config.yaml). Kort:

| Original | Vårt bygg |
|---|---|
| Arduino UNO + CNCShield + 2× Pololu | MKS DLC32 v2.1 + 2× TMC2209 i socket |
| GRBL 0.9i (robotini-fork, servo M3/M5) | FluidNC, servo som ekte Z-akse |
| Servo på digital pin 11 | Servo-signal på gpio.32, 5 V fra ekspansjonsheader |
| Vin-til-+-jumpertriks for servostrøm | Ikke aktuelt |
| Inkscape-plugin + UniversalGcodeSender | Inkscape/vpype → G-code → FluidNC WebUI |
| Steps/mm i EEPROM via `$100=80` | Samme `$100`/`$101`-kommandoer, verifiser med 100 mm-test |

Kalibreringslogikken fra originalens steg 5 gjelder fortsatt: 200-stegs
motor + 20T pulley + GT2 (2 mm pitch) gir teoretisk **80 steps/mm** ved
1/16 microstepping — men TMC2209 i standalone kan stå på annen
microstepping (MS-pinner), så **mål faktisk bevegelse** og juster
forholdsmessig.
