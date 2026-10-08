// Time helpers that work the same on a Mac and on Cloudflare (where the system zone is UTC).

const ISO_WITH_ZONE = /(Z|[+-]\d{2}:?\d{2})$/i;

function zoneOffsetMs(date, timeZone) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone,
      hourCycle: "h23",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
      .formatToParts(date)
      .map((p) => [p.type, p.value]),
  );
  const asUtc = Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second);
  return asUtc - Math.floor(date.getTime() / 1000) * 1000;
}

// "2026-10-10T14:00" is read as wall-clock time in timeZone; strings with Z/offset are taken as is.
export function parseDateTime(value, timeZone) {
  if (ISO_WITH_ZONE.test(value)) return new Date(value);
  const [d, t = "00:00"] = value.split("T");
  const [y, mo, da] = d.split("-").map(Number);
  const [h, mi, s = 0] = t.split(":").map(Number);
  const guess = Date.UTC(y, mo - 1, da, h, mi, s);
  const first = guess - zoneOffsetMs(new Date(guess), timeZone);
  return new Date(guess - zoneOffsetMs(new Date(first), timeZone));
}

export function formatLocal(date, timeZone, allDay = false) {
  return new Intl.DateTimeFormat("de-DE", {
    timeZone,
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    ...(allDay ? {} : { hour: "2-digit", minute: "2-digit" }),
  }).format(date);
}
