# Finnes det offentlig tilgjengelige håndskrift-syntesemodeller som støtter æøå?

*Research-notat, 2026-07-18. Spørsmål: finnes det pretrained modeller (vekter eller hostede tjenester) for håndskriftsyntese som kan skrive æøå i dag?*

## Konklusjon

**Nei.** Ingen offentlig tilgjengelig pretrained modell for håndskriftsyntese med æøå i tegnsettet ble funnet — verken strøkbasert (online) eller rasterbasert (offline). Alle sjekket modeller er trent på engelske datasett (IAM/IAM-OnDB) eller kinesisk/japansk/vietnamesisk. Det finnes heller ikke noe offentlig *trajectory*-datasett med æøå å fine-tune på — data må samles selv.

To delvise lyspunkter:

1. **InkSight (Google)** — åpen modell (Apache-2.0) som konverterer *bilder* av håndskrift til strøk. Ikke tekst-til-håndskrift, men en mulig bro: raster med æøå inn, strøk ut. æøå-dekning udokumentert, men tilnærmingen er glyf-agnostisk (den sporer det den ser).
2. **X-rayLaser-toolkitet** støtter eksplisitt custom datasett og charset — bekreftet i kildekoden. Beste kjøretøy for fine-tune-veien (vei 2).

## Funn per modell

### calligrapher.ai / sjvasquez/handwriting-synthesis

Graves-modellen bak calligrapher.ai. Tegnsettet er hardkodet i [`drawing.py`](https://github.com/sjvasquez/handwriting-synthesis/blob/master/drawing.py): kun ASCII — mellomrom, litt tegnsetting, sifre, A–Z (uten Q og X), a–z. Ingen ikke-ASCII-tegn overhodet. æøå er strukturelt umulig uten retrening.

### X-rayLaser/pytorch-handwriting-synthesis-toolkit

PyTorch-reimplementasjon av Graves. [README](https://github.com/X-rayLaser/pytorch-handwriting-synthesis-toolkit) bekrefter pretrained vekter (`checkpoints/Epoch_46`–`Epoch_56`), trent på IAM-OnDB — altså engelsk charset. Men: tegnsettet er ikke hardkodet — [`handwriting_synthesis/data.py`](https://github.com/X-rayLaser/pytorch-handwriting-synthesis-toolkit/blob/main/handwriting_synthesis/data.py) bygger charset dynamisk fra treningsdataene (`build_charset`), og README dokumenterer custom data provider med 2 metoder. Trening på eget datasett med æøå er en støttet vei, ikke en hack.

### IAM-OnDB (datasettet alt engelsk er trent på)

[Offisiell side (FKI, HEIA-FR)](https://fki.tic.heia-fr.ch/databases/iam-on-line-handwriting-database): tekst fra LOB-korpuset (britisk engelsk, 1978), 221 skribenter, 13 049 tekstlinjer fanget som pennebaner på smartboard. Kun engelsk. Ingen æøå.

### HuggingFace

Modellsøk på «handwriting synthesis/generation» gir tre treff (`3morrrrr/handwriting-synthesis-api`, `iskream23/handwriting_synthesis_network_52`, `finnbusse/handwriting-synthesis-models`) — alle udokumenterte (tomme/manglende model cards), åpenbart re-opplastinger av sjvasquez-vekter. Ingenting med utvidet Latin-charset.

### Diffusjons-/transformermodeller (offline — raster, ubrukelig direkte for plotter)

| Modell | Output | Treningsdata | Vekter | æøå |
|---|---|---|---|---|
| [DiffusionPen](https://github.com/koninik/DiffusionPen) (ECCV 2024) | raster | IAM (engelsk) | [HF](https://huggingface.co/konnik/DiffusionPen) | nei |
| [One-DM](https://github.com/dailenson/One-DM) (ECCV 2024) | raster | engelsk/kinesisk/japansk | GDrive/Baidu | nei |
| [HWT](https://github.com/ankanbhunia/Handwriting-Transformers) (ICCV 2021) | raster | IAM | ja | nei |
| WordStylist | raster | IAM | — | nei |

Alle genererer bilder, ikke strøk. Plotter trenger strøk; vektorisering taper strøkrekkefølge og penndynamikk.

### Strøkbaserte (online) modeller utover Graves

- **[SDT](https://github.com/dailenson/SDT)** (CVPR 2023): genererer online-håndskrift (strøk med skriverekkefølge) med stilimitasjon. Pretrained for kinesisk (CASIA-OLHWDB) pluss japansk/indisk/engelsk skript. Tegnnivå-modell — charset låst til trente tegn. Ingen æøå.
- **HandwritingAgent** ([arXiv 2606.18788](https://arxiv.org/abs/2606.18788), juni 2026): multilingual, genererer strøk direkte som SVG. Lovende retning, men ingen offentlig kode eller vekter funnet per i dag.

### InkSight (Google) — mulig bro

[GitHub](https://github.com/google-research/inksight) / [HF-modell Small-p](https://huggingface.co/Derendering/InkSight-Small-p) (Apache-2.0, TMLR 2025). Konverterer *foto av håndskrift* til digitale strøk («derendering»), ord- og sidenivå, «multi-language support» ifølge README. Ikke en syntesemodell — men den lukker raster-til-strøk-gapet: håndskrevet æøå (eller raster fra diffusjonsmodell) inn, pennebaner ut. Hvorvidt æøå spores korrekt er udokumentert; må testes empirisk. Tracingen er i prinsippet glyf-agnostisk (visuell sporing, ikke charset-oppslag).

### Trajectory-datasett med utvidet Latin (fine-tune-råstoff)

- **Norsk/dansk: ingenting funnet.** NorHand (Nasjonalbiblioteket) er *offline* (skannede bilder) — ubrukelig for strøksyntese.
- **[VNOnDB](https://dl.acm.org/doi/abs/10.1145/3411842)** (vietnamesisk): pennebaner med full diakritikk — beviser at Graves-arkitekturen håndterer diakritiske tegn gitt data, men gir ikke æøå.
- **[OnHW](https://dl.acm.org/doi/abs/10.1145/3411842)** (tysk, Fraunhofer): ordsett med umlauts (59 klasser), men data er IMU-sensorstrømmer fra kulepenn, ikke x/y-baner fra tablet — krever trajectory-rekonstruksjon, upraktisk.
- **IRONOFF** (fransk): online, aksenttegn (éèç), men ikke æøå.

### Kommersielle tjenester

Handwrytten o.l. bruker fonter/roboter og eksponerer ikke strøkdata via API. Ikke relevant.

## Implikasjoner for strek

1. **Vei 1 (komposisjons-hack) står seg.** Ingen snarvei funnet — å syntetisere basisbokstav og legge på ring/skråstrek/ligatur programmatisk i SVG-laget er fortsatt raskeste vei til norsk NN-håndskrift på plotteren.
2. **Vei 2 (fine-tune) krever egen datainnsamling — bekreftet.** Ikke noe eksisterende æøå-trajectory-datasett å låne. X-rayLaser-toolkitet er bekreftet riktig verktøy (custom charset/data provider støttet i koden). VNOnDB-presedensen viser at diakritikk fungerer i arkitekturen.
3. **Ny vei 2b: InkSight som bro.** Skriv æøå-ord for hånd på papir, fotografer, derender til strøk — kan både (a) generere fine-tune-data billigere enn tablet-oppsett, og (b) i teorien brukes direkte: raster-generator med bedre skrift + InkSight = strøk til plotter. Uverifisert for æøå; verdt et lite eksperiment før man bygger datainnsamlingsapp.
