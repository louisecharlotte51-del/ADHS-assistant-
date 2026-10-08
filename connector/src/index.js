#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as icloud from "./icloud.js";
import * as outlook from "./outlook.js";

const server = new McpServer({ name: "adhs-assistant", version: "1.0.0" });

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

const readOnly = { readOnlyHint: true };
const destructive = { destructiveHint: true };
const dateTime = z
  .string()
  .describe("Lokale Zeit wie 2026-10-10T14:00 oder ISO mit Zeitzone. Für ganztägig: 2026-10-10");

// ---------- Outlook ----------

tool("outlook_list_messages", "Listet die neuesten E-Mails aus einem Outlook Ordner (Standard: Posteingang).", {
  folder: z.string().optional().describe("Ordner-ID oder bekannter Name: inbox, sentitems, drafts, deleteditems, junkemail, archive"),
  top: z.number().int().min(1).max(50).optional(),
  unreadOnly: z.boolean().optional().describe("Nur ungelesene"),
}, outlook.listMessages, readOnly);

tool("outlook_search_messages", "Durchsucht alle Outlook E-Mails nach Stichwort, Absender oder Betreff.", {
  query: z.string(),
  top: z.number().int().min(1).max(50).optional(),
}, outlook.searchMessages, readOnly);

tool("outlook_get_message", "Liest eine komplette Outlook E-Mail inklusive Text.", {
  id: z.string(),
}, outlook.getMessage, readOnly);

tool("outlook_list_folders", "Listet alle Outlook Mail-Ordner mit Anzahl ungelesener Mails.", {}, outlook.listFolders, readOnly);

tool("outlook_create_draft", "Erstellt einen E-Mail Entwurf in Outlook (wird NICHT gesendet).", {
  to: z.array(z.string()),
  cc: z.array(z.string()).optional(),
  subject: z.string(),
  body: z.string(),
}, outlook.createDraft);

tool("outlook_send_mail", "Sendet sofort eine E-Mail. Vorher IMMER Empfänger, Betreff und Text dem Nutzer zeigen und ausdrücklich bestätigen lassen.", {
  to: z.array(z.string()),
  cc: z.array(z.string()).optional(),
  subject: z.string(),
  body: z.string(),
}, outlook.sendMail, destructive);

tool("outlook_reply", "Antwortet auf eine E-Mail. Standard: nur Entwurf. sendNow=true sendet sofort, nur nach ausdrücklicher Bestätigung.", {
  id: z.string(),
  body: z.string(),
  replyAll: z.boolean().optional(),
  sendNow: z.boolean().optional(),
}, outlook.reply, destructive);

tool("outlook_mark_read", "Markiert eine E-Mail als gelesen oder ungelesen.", {
  id: z.string(),
  isRead: z.boolean().optional(),
}, outlook.markRead);

tool("outlook_move_message", "Verschiebt eine E-Mail in einen anderen Ordner.", {
  id: z.string(),
  folder: z.string().describe("Ordner-ID oder bekannter Name wie archive"),
}, outlook.moveMessage);

tool("outlook_delete_message", "Verschiebt eine E-Mail in 'Gelöschte Elemente'. Vorher bestätigen lassen.", {
  id: z.string(),
}, outlook.deleteMessage, destructive);

// ---------- Apple iCloud Kalender ----------

tool("calendar_list_calendars", "Listet alle Apple iCloud Kalender.", {}, icloud.listCalendars, readOnly);

tool("calendar_list_events", "Zeigt Termine aus dem Apple iCloud Kalender in einem Zeitraum (inklusive Serientermine).", {
  start: dateTime,
  end: dateTime,
  calendar: z.string().optional().describe("Kalendername. Leer = alle Kalender"),
}, icloud.listEvents, readOnly);

tool("calendar_create_event", "Legt einen neuen Termin im Apple iCloud Kalender an.", {
  title: z.string(),
  start: dateTime,
  end: dateTime.optional().describe("Leer = 1 Stunde nach Start"),
  allDay: z.boolean().optional(),
  calendar: z.string().optional().describe("Kalendername. Leer = Standardkalender"),
  location: z.string().optional(),
  notes: z.string().optional(),
  alarmMinutes: z.number().optional().describe("Erinnerung X Minuten vorher"),
}, icloud.createEvent);

tool("calendar_update_event", "Ändert einen Termin. Die url kommt aus calendar_list_events. Bei Serien wird die ganze Serie geändert.", {
  url: z.string(),
  title: z.string().optional(),
  start: dateTime.optional(),
  end: dateTime.optional(),
  allDay: z.boolean().optional(),
  location: z.string().optional(),
  notes: z.string().optional(),
}, icloud.updateEvent);

tool("calendar_delete_event", "Löscht einen Termin (bei Serien die ganze Serie). Vorher bestätigen lassen.", {
  url: z.string(),
}, icloud.deleteEvent, destructive);

await server.connect(new StdioServerTransport());
