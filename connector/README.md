# 🧠 ADHS Assistant Connector

Verbindet **Claude Desktop (Mac)** mit:

- 📧 **privatem Outlook** (outlook.com, hotmail, live): lesen, suchen, Entwürfe, senden, verschieben, löschen
- 📅 **Apple iCloud Kalender**: Termine ansehen, anlegen, ändern, löschen

Läuft **lokal auf deinem Mac**. Keine Cloud, keine Kosten. Passwörter liegen im **macOS Schlüsselbund**.

⏱️ **Gesamtzeit: ca. 35 Min.**

---

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

- Microsoft Login-Token: `~/.adhs-assistant/msal-cache.json` (nur für dich lesbar)
- Apple Passwort: **macOS Schlüsselbund** (Eintrag `adhs-assistant-icloud`)
- „Löschen“ bei Mails verschiebt nur in **Gelöschte Elemente**.
