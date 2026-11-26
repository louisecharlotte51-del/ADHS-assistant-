# Zentrale – ADHS-Kommandozentrale (Design)

Stand: 2026-11-23 · Status: wartet auf Freigabe

## Wozu (Intent)

Charlotte hat ADHS (mit Medikation, wirkt nicht immer ausreichend) und jongliert viele Lebensbereiche: Uni, Werkstudentin bei Drees & Sommer (Projektmanagement Generalplanung, Mo + Do, 16 Std.), CDU / Junge Union Hamburg-Eppendorf, Privates und das Projekt „ADHS-Assistent".

Ihre Probleme, in ihren Worten:
- Sie **vergisst** viele Dinge und **Fristen**.
- Sie **fängt nicht an**, weil jede Aufgabe wie ein **Riesenberg** wirkt.
- Sie weiß nicht, **womit sie anfangen soll**.

Die Zentrale soll ihr **Denken und Erinnern abnehmen**: alles an einem Ort sehen, Berge in kleine Schritte zerlegen, immer genau **einen** nächsten Schritt zeigen. Vorbild ist ein Video-Dashboard (Sidebar mit Unterbereichen, Kalender, Statuskarten, Pastellfarben, sehr visuell).

## Ziele

1. **„Jetzt"-Ansicht:** zeigt genau einen nächsten Schritt, mit Zeitschätzung und Knöpfen *Fertig / Später / Zu groß? Zerlegen*.
2. **Alles auf einen Blick:** Wochenübersicht mit Fristen, Überfälligem und Zahl offener Aufgaben je Bereich.
3. **Fünf Bereiche:** Uni · Arbeit · Privat · Partei · ADHS-Projekt. Jeder Bereich hat eine eigene Seite und Farbe.
4. **Berg zerlegen:** geführter Dialog („Was ist der allererste Handgriff? Dauert er unter 20 Minuten?"), der eine Aufgabe in Mini-Schritte mit je einer Zeitschätzung teilt.
5. **Fristen mit Wiederholung** (wöchentlich, monatlich) und sichtbarer Dringlichkeit.
6. **Schön und ruhig:** Pastellfarben, Sidebar (am Handy untere Leiste), Karten, Fortschrittsanzeige, kleine Belohnung beim Abhaken.
7. Läuft als **PWA auf iPad/iPhone/Mac**, im Stil von „Fokus Heute" und Praxis-Cockpit.

## Nicht-Ziele (Version 1)

- Kein Server, kein Login, kein Geräte-Sync (Austausch per Backup-Datei wie im Praxis-Cockpit).
- Keine KI-Zerlegung (Ausbau später, Weg C).
- Kein Kalender-Import aus Outlook/Apple (der Connector existiert, Anbindung später).
- Keine Social-Media-Analytik (das war nur das Vorbild-Video, nicht Charlottes Anwendungsfall).
- Keine Medikamenten- oder Gesundheitsdaten.

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es technisch läuft)

- Eine Ansicht, die **mehr Überforderung** auslöst: lange Listen, viele Zahlen, rote Alarmflut.
- Pflege wird zur **zweiten Arbeit**: Eine Aufgabe erfassen muss in unter 10 Sekunden gehen.
- Ein Dashboard, das schön ist, aber nicht sagt, **was jetzt zu tun ist**.
- Schuldgefühl-Design (Streak-Verlust, Strafen, „du hast versagt").

## Randbedingungen

- Statische Dateien, **kein Build-Schritt**, Vanilla HTML/CSS/JS, wie `praxis/` (GitHub Pages).
- Daten nur in `localStorage`, Export/Import als JSON-Datei; Import **führt zusammen**, überschreibt nicht.
- Deutsch, ADHS-Regeln: kurze Texte, max. 3 Aufgaben „Heute", ein nächster Schritt, Listen bis ca. 5 Einträge sichtbar (Rest hinter „mehr").
- Dunkelmodus per `prefers-color-scheme`.
- Offline-fähig (Service Worker).

## Ansätze (verglichen)

| | Ansatz | Vorteil | Nachteil |
|---|---|---|---|
| **A (gewählt)** | Neue PWA im Repo unter `zentrale/` | privat, offline, frei gestaltbar, passt zu bestehenden Apps | kein Sync zwischen Geräten |
| B | Notion-Dashboard | Sync, wie im Video | ADHS-Funktionen und Optik schwer umsetzbar |
| C | A + Claude-Zerlegung | löst das „Berg"-Problem automatisch | braucht Server/API-Key, später als Ausbau auf A |

Charlotte hat A gewählt. Begründung: privat, schnell fertig (erste Version ca. 1–2 Std.), später um C erweiterbar.

## Aufbau (Entscheidungen)

**Ordner:** `zentrale/` mit `index.html`, `style.css`, `app.js`, `sw.js`, `manifest.webmanifest`, `icons/`. Struktur und Navigation folgen `praxis/` (dort gibt es schon Sidebar-Shell, Sheet-Dialog, Toast, Backup).

**Ansichten (Sidebar):**
1. 🎯 **Jetzt** – Begrüßung, eine große Karte „Dein nächster Schritt", darunter Status-Chips (Fristen diese Woche, erledigt heute, offen je Bereich).
2. 📅 **Woche** – Mo–So-Raster mit Fristen und Aufgaben; Mo und Do als „Drees & Sommer"-Tage markiert.
3. 🎓 Uni · 💼 Arbeit · 🏠 Privat · 🏛 Partei · 🧩 ADHS-Projekt – je Bereich eine Liste mit Spalten **Offen / Dran / Fertig**.
4. ⛰️ **Berg zerlegen** – geführter Dialog, erreichbar aus jeder Aufgabe.
5. ⚙️ **Einstellungen** – Backup, Import, Bereichsnamen.

**Datenmodell:**
- Aufgabe: `id, area, title, due?, repeat?, status (todo|doing|done), steps[{id, text, min, done}], createdAt`.
- Fristen sind Aufgaben mit `due`.
- Speicherschlüssel `zentrale-v1`.

**Wahl des „nächsten Schritts" (Regel, einfach und erklärbar):**
1. überfällige Aufgabe, dann
2. Aufgabe mit nächster Frist, dann
3. Aufgabe im Status „Dran", dann
4. älteste offene.

Dann der **erste nicht erledigte Schritt**; hat die Aufgabe keine Schritte, kommt der Hinweis „Zu groß? Zerlegen". Die Karte zeigt immer, warum sie gewählt wurde („Frist in 2 Tagen").

**Schnell erfassen:** Eingabefeld ganz oben auf jeder Seite, Enter speichert, Bereich = aktuelle Seite, Frist optional per Tipp auf „Heute / Morgen / Datum".

**Optik:** Pastell je Bereich (Uni lavendel, Arbeit mint, Privat rosa, Partei sand/gelb, ADHS-Projekt himmelblau), große Rundungen, ruhige Serifenüberschriften wie im Vorbild, viel Weißraum.

**Verknüpfung:** Aus „Jetzt" Knopf „Fokus starten" öffnet `../index.html` (Fokus Heute). README bekommt einen Abschnitt „Zentrale".

## Offen für den Umsetzer

- Genaue Farbwerte, Icons und Schriftwahl.
- Wochenraster auf dem Handy (Liste statt Raster ist okay).
- Tests: Auswahllogik „nächster Schritt" und Wiederholungsfristen sind reine Funktionen und sollten einfache Tests bekommen.

## Meine Entscheidungen (zum Gegenprüfen, Charlotte hat sie nicht ausdrücklich bestätigt)

- Fünf Bereiche inkl. ADHS-Projekt (du nanntest Uni, Arbeit, Privat, Partei und das ADHS-Projekt als Projekt).
- Priorisierungsregel für „Jetzt" wie oben.
- Mo/Do-Markierung für Drees & Sommer fest eingebaut, später einstellbar.
- Keine Gamification mit Strafen; nur kleine Freude beim Abhaken.
- Erste Version ohne Kalender-Import und ohne KI.
