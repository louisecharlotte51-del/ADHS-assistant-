# 🤝 Agenten-Team

Mehrere Claude-Agenten bearbeiten **eine Aufgabe gleichzeitig**, jeder in seinem Gebiet. Funktioniert mit dem Skill **Team Builder**.

## Benutzen (ca. 2 Min.)

1. Claude Code in diesem Repo öffnen (claude.ai/code oder Terminal).
2. Schreiben: `team builder`
3. Gebiete wählen, z. B. `1,3` oder `sicherheit + adhs-ux` (max. 5 Agenten).
4. Aufgabe beschreiben, z. B. „Prüf die Zentrale vor dem nächsten Release“.

→ Alle gewählten Agenten laufen parallel. Am Ende kommt ein gemeinsamer Bericht: Ergebnisse pro Agent, Einigkeit, Widersprüche, nächste Schritte.

## Gebiete

| Ordner | Agenten |
|---|---|
| `entwicklung/` | Software-Architektur, Frontend & PWA, Tests & Qualität, Sicherheit & Datenschutz |
| `design/` | ADHS-UX, Texte & Microcopy |
| `praxis/` | Buchhaltung & Lohn, Social Media (HWG-konform) |
| `organisation/` | Projektplanung, Recherche |

## Neuen Agenten anlegen (ca. 5 Min.)

1. Datei kopieren, z. B. `organisation/recherche.md` → `uni/hausarbeit.md` (neuer Ordner = neues Gebiet).
2. Erste Zeile `# Name` und den Satz darunter anpassen (das zeigt das Menü an).
3. *Identität*, *Regeln*, *Arbeitsweise* anpassen. *Team-Regeln* und *Lieferergebnis* so lassen.

Der Team Builder findet neue Dateien automatisch.

## In anderen Projekten nutzen

Ordner `agents/` ins andere Repo kopieren. Oder für alle Projekte: nach `~/.claude/agents/` kopieren.
