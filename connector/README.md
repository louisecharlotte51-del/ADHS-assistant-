# 🧠 ADHS Assistant Connector

Verbindet **Claude** (iPad, iPhone, Mac, Cowork) mit:

- 📧 **privatem Outlook** (outlook.com, hotmail, live): lesen, suchen, Entwürfe, senden, verschieben, löschen
- 📅 **Apple iCloud Kalender**: Termine ansehen, anlegen, ändern, löschen

Zwei Varianten, gleicher Funktionsumfang:

- ☁️ **Cloud (Cloudflare):** funktioniert auf **iPad, iPhone, Mac** und in **Cowork**. Einrichtung komplett im Browser. **ca. 25 Min.**
- 💻 **Lokal (Mac):** maximale Privatsphäre, nur Claude Desktop. **ca. 35 Min.**

---

# ☁️ Cloud-Variante (iPad tauglich)

## ✅ Schritt 1: Cloudflare Konto (5 Min.)

1. Öffne **https://dash.cloudflare.com/sign-up** und lege ein **kostenloses Konto** an.
2. E-Mail bestätigen.

## ✅ Schritt 2: Connector online stellen (7 Min.)

1. In Cloudflare: **Compute (Workers)** → **Workers & Pages** → **Erstellen**.
2. **Repository importieren** → **GitHub verbinden** → Repo **ADHS-assistant-** wählen.
3. Einstellungen:
   - Projektname: **adhs-assistant** (genau so)
   - Root directory: **leer lassen** (die `wrangler.toml` im Hauptordner zeigt schon auf `connector/`)
   - Build-Befehl: leer lassen. Bereitstellungsbefehl: `npx wrangler deploy`
4. **Bereitstellen** tippen und ca. **2 Min.** warten.
5. Die Adresse notieren, z. B. `https://adhs-assistant.DEINNAME.workers.dev`

## ✅ Schritt 3: Geheimen Schlüssel setzen (3 Min.)

1. Im Worker: **Einstellungen** → **Variablen und Geheimnisse** → **Hinzufügen**.
2. Typ **Geheimnis**, Name `ACCESS_KEY`.
3. Wert: ein **langes Zufallspasswort** (mind. **30 Zeichen**, z. B. aus der iPhone **Passwörter** App).
4. **Bereitstellen** tippen.

## ✅ Schritt 4: Einrichtungsseite (10 Min.)

Öffne in Safari: `https://adhs-assistant.DEINNAME.workers.dev/setup/DEIN-ACCESS-KEY`

Die Seite führt dich durch 3 Kärtchen:

1. 📅 **Apple Kalender** verbinden (App-Passwort, siehe unten Schritt 4 der lokalen Variante).
2. 📧 **Outlook** verbinden (Microsoft App, siehe unten Schritt 3 der lokalen Variante).
3. 🔌 **URL kopieren** und in Claude unter **Einstellungen → Connectors → Eigenen Connector hinzufügen** einfügen.

🔒 Die Connector-URL enthält deinen Schlüssel. **Nicht teilen.**

---

# 💻 Lokale Variante (Mac)

## ✅ Schritt 1: Node.js installieren (5 Min.)

1. Öffne **nodejs.org** und lade die **LTS Version** für Mac.
2. Installer doppelklicken, durchklicken.
3. Test im **Terminal**: `node -v` zeigt eine Zahl ab **20**.

## ✅ Schritt 2: Code auf den Mac holen (3 Min.)

Im **Terminal**:

```bash
cd ~
git clone https://github.com/louisecharlotte51-del/ADHS-assistant-.git
cd ADHS-assistant-/connector
npm install
```

## ✅ Schritt 3: Microsoft App anlegen (10 Min.)

1. Öffne **https://entra.microsoft.com** und melde dich mit deinem **Outlook Konto** an.
   - Falls kein Zugang: vorher kostenloses Konto auf **https://azure.microsoft.com/free** anlegen.
2. **App-Registrierungen** → **Neue Registrierung**.
3. Name: `ADHS Assistant`.
4. Kontotypen: **Nur persönliche Microsoft-Konten**.
5. Umleitungs-URI: **leer lassen** → **Registrieren**.
6. Links **Authentifizierung** → ganz unten **Öffentliche Clientflows zulassen** = **Ja** → **Speichern**.
7. Auf **Übersicht** die **Anwendungs-ID (Client-ID)** kopieren.

## ✅ Schritt 4: Apple App-Passwort (3 Min.)

1. Öffne **https://account.apple.com** → **Anmeldung und Sicherheit**.
2. **App-spezifische Passwörter** → **+** → Name `Claude`.
3. Passwort kopieren (Format `xxxx-xxxx-xxxx-xxxx`).

## ✅ Schritt 5: Einrichtungs-Assistent (5 Min.)

```bash
npm run setup
```

Der Assistent fragt nacheinander:

1. 📧 **Client-ID** einfügen → Link öffnen → Code eingeben → mit Outlook anmelden.
2. 📅 **Apple-ID** und **App-Passwort** einfügen.

Am Ende siehst du deine **Kalendernamen**. 🎉

## ✅ Schritt 6: In Claude Desktop eintragen (5 Min.)

1. Im Terminal den Node Pfad holen: `which node` (z. B. `/usr/local/bin/node`).
2. In Claude Desktop: **Einstellungen** → **Entwickler** → **Konfiguration bearbeiten**.
3. Diesen Block einfügen (**DEINNAME** und Node Pfad anpassen):

```json
{
  "mcpServers": {
    "adhs-assistant": {
      "command": "/usr/local/bin/node",
      "args": ["/Users/DEINNAME/ADHS-assistant-/connector/src/index.js"]
    }
  }
}
```

4. Claude Desktop **komplett beenden** (⌘Q) und neu starten.
5. Im Chat unter **🔌 Connectors** sollte **adhs-assistant** erscheinen.

---

## 🗣️ Probier es aus

- „Was steht **diese Woche** in meinem Kalender?“
- „Zeig mir meine **ungelesenen Mails** von heute.“
- „Trag **Zahnarzt Freitag 10 Uhr** ein, Erinnerung **30 Min.** vorher.“
- „Schreib einen **Entwurf** als Antwort auf die Mail von Anna.“

## 🤖 Text für die Projekt-Anweisungen deines Personal Assistant

```text
Du hast Zugriff auf mein privates Outlook (Tools outlook_*) und meinen Apple Kalender (Tools calendar_*).
Starte jede Tagesplanung mit calendar_list_events für heute und morgen.
Bevor du eine Mail sendest oder etwas löschst, zeig mir alles und frag mich mit Ja/Nein.
Lieber Entwürfe als direkt senden.
```

## 🛟 Hilfe bei Problemen

- **„Nicht bei Microsoft angemeldet“** → im Ordner `connector` ausführen: `npm run login`
- **„iCloud nicht eingerichtet“** → `npm run setup` erneut starten.
- **Connector fehlt in Claude** → Pfade in der Konfiguration prüfen, Claude mit ⌘Q neu starten.
- **Zugriff widerrufen** → Apple App-Passwort löschen bzw. Microsoft App-Registrierung löschen.

## 🔒 Sicherheit

**Cloud:**

- Zugriff nur mit deinem **ACCESS_KEY** in der URL.
- Apple App-Passwort und Microsoft Token liegen im **Cloudflare KV Speicher** deines Kontos.
- Neuer Schlüssel = alle alten Links ungültig: einfach `ACCESS_KEY` ändern.

**Lokal:**

- Microsoft Login-Token: `~/.adhs-assistant/msal-cache.json` (nur für dich lesbar)
- Apple Passwort: **macOS Schlüsselbund** (Eintrag `adhs-assistant-icloud`)
- „Löschen“ bei Mails verschiebt nur in **Gelöschte Elemente**.
