# Projektstand Gartenquartier Bergfrieden (Übergabe für neue Sitzungen)

Stand: 28.11.2026 · Branch `claude/stoic-fermat-pe2j98` · Sprache: Deutsch, ADHS-Format (kurz, nummeriert, erster Satz = nächste Aktion)

## Aufgabe
Entwurfsstudie neues Stadtquartier auf der Kleingartenkolonie Bergfrieden (Berlin-Tempelhof, südl. Tempelhofer Feld) bis zum Teltowkanal.
Grundlage ist das Handblatt der Entwerferin (Skizze bleibt das Gerüst):
- **Bewegungsader** Komturstraße (Auto/Rad/Fuß, Tempo 30, Straßenbegleitgrün), neuer S-Bahn-Halt Komturstraße im Norden
- **Wasserader** Tempelhofer Feld → Teltowkanal, Äste und Schwammflächen zwischen den Baufeldern
- **Erholungsader** Ost-West (Biodiversität, Ruhe, Parks verbinden)
- **Trichter** öffentlich → privat, **Quartiershauptplatz** am Kanal (Grün, Gastro, Retention, Gewerbe)
- 13 polygonale Baufelder (9,1 ha), Phasen P0 2027–29 … P4 2038–42 von der S-Bahn zum Kanal
- Kleingärten: KEP 2030 Kategorie 1 (dauerhaft gesichert) → FNP-Änderung + Ersatzland nötig

## Ergebnisse (alle in `gartenquartier/`)
| Stand | Inhalt | Seite |
|---|---|---|
| V1–V5 | 5 Bebauungsvarianten, Regeln, Phasen, Blender | https://claude.ai/artifact/7XSSdVs4tovei1V22WfnYk |
| V6–V8 | 3 Varianten ohne Höfe, Nutzungskonzept, Phase 1 im Detail | https://claude.ai/artifact/GSak6PnuiRjjSXa6nLtkD7 |
| Fünf Quartiere | Neuer Plan (A, Q1–5, Stadtwald): Typologien je Quartier, Achsenschnitte, Wasserkette, Q4-Themen, DXF für Vectorworks (`fuenf_quartiere/`) | https://claude.ai/artifact/HzCV9feEQuiFhYSDUQ6FZs |
| Konzept I | Euer 5-Quartiere-Plan georeferenziert (±3 m), 18 Baufelder; Varianten A „Kante und Garten“ / B „Nachbarschaften“, S-Bahn (A100-Deckel, Stationsbrücke, 2 Landschaftsbrücken), Regelwerk Erschließung + Öffentlichkeit, Schnitte 1:500, Piktogramme, 6 Perspektiven + Nano-Banana-Prompts (`konzept1/`) | https://claude.ai/artifact/WG3U9dYhMNK6wmKjbAqG6e |
| S1–S6 | 6 Schwarzpläne (Typologie-Mix), Höhenpläne, Schnitte A–D, 3D-Modell, Luftbilder, Schnittperspektiven, 5 Situationsskizzen | https://claude.ai/artifact/QEXWAqikMT72k4kAQZ23eb |

Dateien zum Weitergeben: `schwarzplaene_S1-S6.pdf`, `situationen_renderings.pdf`, `bergfrieden_3d_FBX.zip`, `bergfrieden_3d_OBJ.zip`, `3d/bergfrieden_typologien_S1-S6.blend`.

## Konzept I (`konzept1/`, Stand 28.11.)
Reihenfolge: `georef.py` → `digitalisieren.py` → `felder.py` → `bebauung.py` → `geruest.py` → `plaene.py` → `blaetter.py` → `dxf_export.py` → `szene_k1.py` → `blender -b --python blender_k1.py -- --render | --export`.
Kanten je Baufeld stehen von Hand in `SPEC` (bebauung.py): k = immer geschlossen, s = Seitenachse (A geschlossen, B Kopfbauten), o = offen.
Ergebnisse in `konzept1/out/`: Pläne maßstäblich als PDF, DXF (lokaler Nullpunkt 391250 / 5813550), FBX/OBJ-Zip, .blend, Seite `index.html`.
Kennwerte A: ca. 1.150 WE, GFZ 1,51 netto / 0,62 brutto, Feuerwehr 109/109. B: ca. 1.100 WE.
Offen: Variante wählen; DXF der Baufelder aus Vectorworks; A100-Deckel bestätigen; Hallen im Stadtwald (8.400 m²) entfallen?; Literatur-Ordner fehlt; Konzept II „Höfe“ folgt.

## Konzept I, Stand 2 (28.11. abends) – aktueller Stand
Feedback der Nutzerin: zu wenig Bebauung, Typologien zu ähnlich, Bahnhof 90° drehen + spektakulärer, Kanal mit Steg, Designsystem nutzen.
Reihenfolge: `bebauung2.py` (Regelwerk R1–R6, Typologie je Quartier) → `ufer.py` → `plaene2.py` (Designsystem) → `K=2 python3 szene_k1.py` →
`blender -b --python blender_k1.py -- --render --k2` / `--export --k2` → `K=2 python3 dxf_export.py`. Ergebnisse in `konzept1/out2/`. Seite: https://claude.ai/artifact/HhQmM6PExudPfZ1krNhhY6
Kennwerte: GFZ 2,22 netto / 0,91 brutto, ca. 1.810 WE. Typologien: A Sockel+Scheibe+Turm, Q1 Werkblock, Q2 Platzrand+Winkel,
Q3 Zeilenhof (Kopfbau, Stadthäuser, Punkthäuser am Wald), Q4 Gartenhof offen nach Süden, Q5 Kamm zum Wasser.
Bahnhof: Blattdach 190 × 60 m längs der Gleise. Ufer: Badebucht 70 × 20 m mit Badeschiff 32,5 × 8,2 m hinter der Uferlinie.
Designsystem: https://claude.ai/artifact/SV9KP2gEM8xT9AKPRm693y · Drive: „Südring: Konzepte für Hannover“ (Hof-Regelwerk), „Literaturzusammenfassung“.
Hinweis: Ecovillage Hannover wurde nie gebaut (Insolvenz 2024); Oberbillwerder Hamburg ist das bessere Vorbild.

## Skripte (Reihenfolge)
1. `entwurf.py` Gerüst (Adern, Baufelder, Phasen) aus `daten/` (Geoportal Berlin, EPSG:25833)
2. `varianten.py` V1–V5 · `varianten2.py` V6–V8 · `nutzungen.py` Nutzungen · `typologien.py` S1–S6
3. Zeichnungen: `zeichnungen.py`, `zeichnungen2.py`, `schwarzplaene.py`, `schwarzplan_schnitte.py`
4. 3D: `situationen.py` → `3d/szene3.json`, dann `blender -b --python blender_typologien.py -- --luft | --situationen | --export | --fbx`
5. `skizzen_nachbearbeitung.py`, Seiten: `web_build.py`, `web_build2.py`, `web_build3.py`; PDF: `situationen_pdf.py`

Kennwerte: EG 4,2 m, OG 3,1 m, 88 m² BGF/WE, 1,9 EW/WE, Abstandsflächen 0,4 H (BauO Bln). Lokaler 3D-Nullpunkt = (391250, 5813550).

## Offen / letzte Frage an die Nutzerin
- Passen die Situationsskizzen (z. B. Bewegungsader)? Welche Variante soll weiter ausgearbeitet werden?
- Skizzen-Staffage ist Blockfiguren-Niveau (Arbeitsstand).

Miro-Board des Teams: https://miro.com/app/board/uXjVEQYDCGs=/ (Frame 3: S-Bahn-Ideen, Konzept I „Grüne Adern“, Leitideen/Phasen)
