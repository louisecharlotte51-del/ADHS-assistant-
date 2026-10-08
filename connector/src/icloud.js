import crypto from "node:crypto";
import ICAL from "ical.js";
import { createDAVClient } from "tsdav";
import { readConfig, readIcloudPassword } from "./config.js";

const MAX_OCCURRENCES = 500;
const LOCAL_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone;

let clientPromise;

function getClient() {
  if (!clientPromise) {
    const { icloudUser } = readConfig();
    const password = icloudUser && readIcloudPassword(icloudUser);
    if (!icloudUser || !password) {
      throw new Error("iCloud Kalender ist noch nicht eingerichtet. Bitte im Terminal 'npm run setup' ausführen.");
    }
    clientPromise = createDAVClient({
      serverUrl: "https://caldav.icloud.com",
      credentials: { username: icloudUser, password },
      authMethod: "Basic",
      defaultAccountType: "caldav",
    }).catch((err) => {
      clientPromise = undefined;
      throw err;
    });
  }
  return clientPromise;
}

async function eventCalendars() {
  const client = await getClient();
  const calendars = await client.fetchCalendars();
  return calendars.filter((c) => !c.components || c.components.includes("VEVENT"));
}

async function findCalendar(name) {
  const calendars = await eventCalendars();
  if (!name) return calendars[0];
  const match = calendars.find(
    (c) => String(c.displayName).toLowerCase() === name.toLowerCase(),
  );
  if (!match) {
    throw new Error(
      `Kalender "${name}" nicht gefunden. Vorhanden: ${calendars.map((c) => c.displayName).join(", ")}`,
    );
  }
  return match;
}

export async function listCalendars() {
  const calendars = await eventCalendars();
  return calendars.map((c) => ({ name: c.displayName, farbe: c.calendarColor, url: c.url }));
}

function formatLocal(date, allDay) {
  return new Intl.DateTimeFormat("de-DE", {
    timeZone: LOCAL_TZ,
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    ...(allDay ? {} : { hour: "2-digit", minute: "2-digit" }),
  }).format(date);
}

function registerTimezones(vcalendar) {
  for (const vtz of vcalendar.getAllSubcomponents("vtimezone")) {
    const tz = new ICAL.Timezone(vtz);
    if (!ICAL.TimezoneService.has(tz.tzid)) ICAL.TimezoneService.register(tz);
  }
}

function toEntry(item, start, end, url) {
  const allDay = start.isDate;
  const startDate = start.toJSDate();
  const endDate = end.toJSDate();
  return {
    titel: item.summary,
    start: formatLocal(startDate, allDay),
    ende: formatLocal(allDay ? new Date(endDate.getTime() - 1) : endDate, allDay),
    startIso: startDate.toISOString(),
    endeIso: endDate.toISOString(),
    ganztaegig: allDay,
    ort: item.location || undefined,
    notizen: item.description || undefined,
    wiederkehrend: item.isRecurring() || undefined,
    url,
  };
}

// Turns one CalDAV object into the concrete occurrences inside [from, to].
function expandObject(obj, from, to, calendarName) {
  const vcalendar = new ICAL.Component(ICAL.parse(obj.data));
  registerTimezones(vcalendar);
  const vevents = vcalendar.getAllSubcomponents("vevent");
  const master = vevents.find((v) => !v.hasProperty("recurrence-id")) || vevents[0];
  if (!master) return [];
  const event = new ICAL.Event(master);
  for (const v of vevents) {
    if (v !== master && v.hasProperty("recurrence-id")) event.relateException(new ICAL.Event(v));
  }

  const results = [];
  const push = (item, s, e) => {
    if (s.toJSDate() <= to && e.toJSDate() >= from) {
      results.push({ kalender: calendarName, ...toEntry(item, s, e, obj.url) });
    }
  };

  if (!event.isRecurring()) {
    push(event, event.startDate, event.endDate);
    return results;
  }
  const it = event.iterator();
  for (let next = it.next(), n = 0; next && n < MAX_OCCURRENCES; next = it.next(), n++) {
    if (next.toJSDate() > to) break;
    const details = event.getOccurrenceDetails(next);
    push(details.item, details.startDate, details.endDate);
  }
  return results;
}

export async function listEvents({ start, end, calendar }) {
  const client = await getClient();
  const from = new Date(start);
  const to = new Date(end);
  const calendars = calendar ? [await findCalendar(calendar)] : await eventCalendars();
  const all = [];
  for (const cal of calendars) {
    const objects = await client.fetchCalendarObjects({
      calendar: cal,
      timeRange: { start: from.toISOString(), end: to.toISOString() },
    });
    for (const obj of objects) {
      if (obj.data) all.push(...expandObject(obj, from, to, cal.displayName));
    }
  }
  return all.sort((a, b) => a.startIso.localeCompare(b.startIso));
}

function icsDate(date) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

function icsDay(value) {
  return value.slice(0, 10).replace(/-/g, "");
}

function escapeText(text) {
  return String(text).replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/([,;])/g, "\\$1");
}

function addDays(isoDay, days) {
  const d = new Date(`${isoDay.slice(0, 10)}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export async function createEvent({ calendar, title, start, end, allDay = false, location, notes, alarmMinutes }) {
  const client = await getClient();
  const cal = await findCalendar(calendar);
  const uid = crypto.randomUUID();
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//ADHS Assistant//DE",
    "BEGIN:VEVENT",
    `UID:${uid}`,
    `DTSTAMP:${icsDate(new Date())}`,
    `SUMMARY:${escapeText(title)}`,
  ];
  if (allDay) {
    // DTEND is exclusive for all-day events, so the end day is pushed by one.
    lines.push(`DTSTART;VALUE=DATE:${icsDay(start)}`);
    lines.push(`DTEND;VALUE=DATE:${icsDay(addDays(end || start, 1))}`);
  } else {
    const s = new Date(start);
    const e = end ? new Date(end) : new Date(s.getTime() + 60 * 60 * 1000);
    lines.push(`DTSTART:${icsDate(s)}`, `DTEND:${icsDate(e)}`);
  }
  if (location) lines.push(`LOCATION:${escapeText(location)}`);
  if (notes) lines.push(`DESCRIPTION:${escapeText(notes)}`);
  if (alarmMinutes != null) {
    lines.push(
      "BEGIN:VALARM",
      "ACTION:DISPLAY",
      `DESCRIPTION:${escapeText(title)}`,
      `TRIGGER:-PT${Math.round(alarmMinutes)}M`,
      "END:VALARM",
    );
  }
  lines.push("END:VEVENT", "END:VCALENDAR");

  const res = await client.createCalendarObject({
    calendar: cal,
    filename: `${uid}.ics`,
    iCalString: lines.join("\r\n") + "\r\n",
  });
  if (!res.ok) throw new Error(`iCloud Fehler ${res.status}: ${await res.text()}`);
  return { erstellt: true, kalender: cal.displayName, url: new URL(`${uid}.ics`, cal.url).href };
}

async function fetchObject(url) {
  const client = await getClient();
  const calendars = await eventCalendars();
  const cal = calendars.find((c) => url.startsWith(c.url));
  if (!cal) throw new Error("Termin gehört zu keinem bekannten Kalender.");
  const [obj] = await client.fetchCalendarObjects({ calendar: cal, objectUrls: [url] });
  if (!obj?.data) throw new Error("Termin nicht gefunden.");
  return { client, obj };
}

export async function updateEvent({ url, title, start, end, allDay, location, notes }) {
  const { client, obj } = await fetchObject(url);
  const vcalendar = new ICAL.Component(ICAL.parse(obj.data));
  registerTimezones(vcalendar);
  const vevents = vcalendar.getAllSubcomponents("vevent");
  const master = vevents.find((v) => !v.hasProperty("recurrence-id")) || vevents[0];
  const event = new ICAL.Event(master);

  if (title != null) event.summary = title;
  if (location != null) event.location = location;
  if (notes != null) event.description = notes;
  const isAllDay = allDay ?? event.startDate.isDate;
  if (start != null || end != null || allDay != null) {
    const duration = event.endDate.toJSDate() - event.startDate.toJSDate();
    if (isAllDay) {
      const startDay = (start ?? event.startDate.toString()).slice(0, 10);
      const endDay = end ? end.slice(0, 10) : addDays(startDay, Math.max(1, Math.round(duration / 864e5)) - 1);
      master.updatePropertyWithValue("dtstart", ICAL.Time.fromDateString(startDay));
      master.updatePropertyWithValue("dtend", ICAL.Time.fromDateString(addDays(endDay, 1)));
    } else {
      const s = start ? new Date(start) : event.startDate.toJSDate();
      const e = end ? new Date(end) : new Date(s.getTime() + duration);
      master.updatePropertyWithValue("dtstart", ICAL.Time.fromJSDate(s, true));
      master.updatePropertyWithValue("dtend", ICAL.Time.fromJSDate(e, true));
    }
  }
  master.updatePropertyWithValue("dtstamp", ICAL.Time.fromJSDate(new Date(), true));

  const res = await client.updateCalendarObject({
    calendarObject: { url: obj.url, etag: obj.etag, data: vcalendar.toString() },
  });
  if (!res.ok) throw new Error(`iCloud Fehler ${res.status}: ${await res.text()}`);
  return { aktualisiert: true, serieGeaendert: event.isRecurring() || undefined };
}

export async function deleteEvent({ url }) {
  const { client, obj } = await fetchObject(url);
  const res = await client.deleteCalendarObject({ calendarObject: { url: obj.url, etag: obj.etag } });
  if (!res.ok) throw new Error(`iCloud Fehler ${res.status}: ${await res.text()}`);
  return { geloescht: true };
}
