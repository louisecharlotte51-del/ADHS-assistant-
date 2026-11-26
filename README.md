# 🎯 Fokus Heute

ADHS-freundliche Web-App (PWA) für iPhone und iPad. Läuft komplett im Browser, Daten bleiben **nur lokal** auf dem Gerät.

- ☀️ **Morgenplanung:** max. 3 Aufgaben
- 👣 **Ein nächster Schritt** pro Aufgabe + Fertig-Kriterium (max. 3 Punkte)
- ⏱️ **Fokus-Timer:** 20 Min Arbeit, 5 Min Pause, harter Stopp mit Ton
- 🎉 **Belohnung** beim Abhaken

## Auf dem iPad installieren
1. GitHub: **Settings → Pages → Branch `main` / root → Save**
2. Safari öffnen: `https://<benutzername>.github.io/<repo>/`
3. **Teilen-Symbol → Zum Home-Bildschirm**

🔈 Ton: Stummschalter am Gerät aus, Lautstärke an.

## 🔌 Outlook + Apple Kalender für Claude

👉 Connector für **privates Outlook + Apple iCloud Kalender**: siehe [connector/README.md](connector/README.md)

## 🏥 Praxis-Cockpit (Sinologikum)

Zweite App im Ordner [`praxis/`](praxis/): **Buchhaltung, Lohn, Social Media, Fristen** an einem Ort.

- 📒 **Monats-Checkliste** Buchhaltung (TCM Soft, Kontoabgleich, DATEV Unternehmen online)
- 💶 **Lohn:** Stunden, Urlaub, Krank pro Person + Text zum Kopieren für den Steuerberater
- 📣 **Social Media:** Idee → Entwurf → Geplant → Live, TCM-Jahreszeiten-Ideen, HWG-Check
- ✅ **Fristen** mit Wiederholung (monatlich, vierteljährlich …)
- 💾 **Team-Austausch** per Backup-Datei (iCloud Drive), Import führt zusammen

📲 Öffnen: `https://<benutzername>.github.io/<repo>/praxis/` → **Teilen → Zum Home-Bildschirm**
💻 Mac (Safari): **Ablage → Zum Dock hinzufügen**

🔒 Daten bleiben **nur auf dem Gerät**. **Keine Patientendaten** eintragen.

## 🎯 Zentrale (ADHS-Kommandozentrale)

Dritte App im Ordner [`zentrale/`](zentrale/): **Uni, Arbeit, Privat, Partei und ADHS-Projekt** an einem Ort.

- 🎯 **Jetzt:** genau **ein** nächster Schritt (überfällig → nächste Frist → „Dran" → älteste)
- ⛰️ **Berg zerlegen:** geführter Dialog in Mini-Schritte mit Zeitschätzung
- 📅 **Woche:** Fristen im Überblick, Mo + Do als Dresden-Sommer-Tage markiert
- 🔁 Fristen mit Wiederholung, 💾 Backup/Import per Datei (führt zusammen)
- 📅 **Apple-Kalender** in Jetzt + Woche (nur lesen, über den Connector, Route `/calendar/<Schlüssel>`)

📲 Öffnen: `https://<benutzername>.github.io/<repo>/zentrale/` → **Teilen → Zum Home-Bildschirm**
🧪 Logik-Tests: `node --test zentrale/test/logic.test.js`

### ✨ Claude zerlegt Aufgaben (optional, ca. 10 Min.)

Nutzt den Cloudflare-Connector (Route `/split/<Schlüssel>`). Kosten: unter 1 Cent pro Zerlegung, Tageslimit im Server 100 Anfragen.

1. **API-Key anlegen:** console.anthropic.com → *Settings → Limits* → **Monthly spend limit 5 €** setzen → *API Keys → Create Key*.
2. **In Cloudflare eintragen:** Worker `adhs-assistant` → *Settings → Variables and Secrets* → **Add** → Typ **Secret**, Name `ANTHROPIC_API_KEY`, Wert = der Key → *Deploy*.
3. **In der Zentrale verbinden:** *Einstellungen → Claude zerlegt für dich* → Connector-Link (`…/setup/…` oder `…/mcp/…`) einfügen → *Speichern*.
4. In „Berg zerlegen" erscheint **✨ Claude schlägt Schritte vor**.

🔒 Gesendet wird nur der Titel der Aufgabe. Der Link wird nur auf diesem Gerät gespeichert (nicht im Backup).
🧪 Tests: `node --test connector/test/split.test.js`
