import { z } from "zod";

const readOnly = { readOnlyHint: true };
const destructive = { destructiveHint: true };
const dateTime = z
  .string()
  .describe("Lokale Zeit wie 2026-10-10T14:00 oder ISO mit Zeitzone. Für ganztägig: 2026-10-10");

/**
 * Registers all Outlook + iCloud tools. outlook() and icloud() return the service
 * objects, so the cloud Worker can build them lazily per request.
 */
export function registerTools(server, { outlook, icloud }) {
  function tool(name, description, inputSchema, handler, annotations = {}) {
    server.registerTool(name, { description, inputSchema, annotations }, async (args) => {
      try {
        const result = await handler(args);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { isError: true, content: [{ type: "text", text: String(err?.message || err) }] };
      }
    });
  }

  // ---------- Outlook ----------

  tool("outlook_list_messages", "Listet die neuesten E-Mails aus einem Outlook Ordner (Standard: Posteingang).", {
    folder: z.string().optional().describe("Ordner-ID oder bekannter Name: inbox, sentitems, drafts, deleteditems, junkemail, archive"),
    top: z.number().int().min(1).max(50).optional(),
    unreadOnly: z.boolean().optional().describe("Nur ungelesene"),
  }, (a) => outlook().listMessages(a), readOnly);

  tool("outlook_search_messages", "Durchsucht alle Outlook E-Mails nach Stichwort, Absender oder Betreff.", {
    query: z.string(),
    top: z.number().int().min(1).max(50).optional(),
  }, (a) => outlook().searchMessages(a), readOnly);

  tool("outlook_get_message", "Liest eine komplette Outlook E-Mail inklusive Text.", {
    id: z.string(),
  }, (a) => outlook().getMessage(a), readOnly);

  tool("outlook_list_folders", "Listet alle Outlook Mail-Ordner mit Anzahl ungelesener Mails.", {}, (a) => outlook().listFolders(a), readOnly);

  tool("outlook_create_draft", "Erstellt einen E-Mail Entwurf in Outlook (wird NICHT gesendet).", {
    to: z.array(z.string()),
    cc: z.array(z.string()).optional(),
    subject: z.string(),
    body: z.string(),
  }, (a) => outlook().createDraft(a));

  tool("outlook_send_mail", "Sendet sofort eine E-Mail. Vorher IMMER Empfänger, Betreff und Text dem Nutzer zeigen und ausdrücklich bestätigen lassen.", {
    to: z.array(z.string()),
    cc: z.array(z.string()).optional(),
    subject: z.string(),
    body: z.string(),
  }, (a) => outlook().sendMail(a), destructive);

  tool("outlook_reply", "Antwortet auf eine E-Mail. Standard: nur Entwurf. sendNow=true sendet sofort, nur nach ausdrücklicher Bestätigung.", {
    id: z.string(),
    body: z.string(),
    replyAll: z.boolean().optional(),
    sendNow: z.boolean().optional(),
  }, (a) => outlook().reply(a), destructive);

  tool("outlook_mark_read", "Markiert eine E-Mail als gelesen oder ungelesen.", {
    id: z.string(),
    isRead: z.boolean().optional(),
  }, (a) => outlook().markRead(a));

  tool("outlook_move_message", "Verschiebt eine E-Mail in einen anderen Ordner.", {
    id: z.string(),
    folder: z.string().describe("Ordner-ID oder bekannter Name wie archive"),
  }, (a) => outlook().moveMessage(a));

  tool("outlook_delete_message", "Verschiebt eine E-Mail in 'Gelöschte Elemente'. Vorher bestätigen lassen.", {
    id: z.string(),
  }, (a) => outlook().deleteMessage(a), destructive);

  // ---------- Apple iCloud Kalender ----------

  tool("calendar_list_calendars", "Listet alle Apple iCloud Kalender.", {}, (a) => icloud().listCalendars(a), readOnly);

  tool("calendar_list_events", "Zeigt Termine aus dem Apple iCloud Kalender in einem Zeitraum (inklusive Serientermine).", {
    start: dateTime,
    end: dateTime,
    calendar: z.string().optional().describe("Kalendername. Leer = alle Kalender"),
  }, (a) => icloud().listEvents(a), readOnly);

  tool("calendar_create_event", "Legt einen neuen Termin im Apple iCloud Kalender an.", {
    title: z.string(),
    start: dateTime,
    end: dateTime.optional().describe("Leer = 1 Stunde nach Start"),
    allDay: z.boolean().optional(),
    calendar: z.string().optional().describe("Kalendername. Leer = Standardkalender"),
    location: z.string().optional(),
    notes: z.string().optional(),
    alarmMinutes: z.number().optional().describe("Erinnerung X Minuten vorher"),
  }, (a) => icloud().createEvent(a));

  tool("calendar_update_event", "Ändert einen Termin. Die url kommt aus calendar_list_events. Bei Serien wird die ganze Serie geändert.", {
    url: z.string(),
    title: z.string().optional(),
    start: dateTime.optional(),
    end: dateTime.optional(),
    allDay: z.boolean().optional(),
    location: z.string().optional(),
    notes: z.string().optional(),
  }, (a) => icloud().updateEvent(a));

  tool("calendar_delete_event", "Löscht einen Termin (bei Serien die ganze Serie). Vorher bestätigen lassen.", {
    url: z.string(),
  }, (a) => icloud().deleteEvent(a), destructive);
}
