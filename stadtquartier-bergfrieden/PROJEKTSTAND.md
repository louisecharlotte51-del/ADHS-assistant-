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
| S1–S6 | 6 Schwarzpläne (Typologie-Mix), Höhenpläne, Schnitte A–D, 3D-Modell, Luftbilder, Schnittperspektiven, 5 Situationsskizzen | https://claude.ai/artifact/QEXWAqikMT72k4kAQZ23eb |

Dateien zum Weitergeben: `schwarzplaene_S1-S6.pdf`, `situationen_renderings.pdf`, `bergfrieden_3d_FBX.zip`, `bergfrieden_3d_OBJ.zip`, `3d/bergfrieden_typologien_S1-S6.blend`.

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
