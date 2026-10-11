'use strict';
// Praxis-Cockpit: Daten bleiben lokal auf dem Gerät (localStorage).
// Team-Austausch per Backup-Datei: Import führt zusammen, die neueste Änderung gewinnt.

const KEY = 'praxis-cockpit-v1';
const DEVICE_KEY = 'praxis-cockpit-device';
const COLLS = ['meta', 'team', 'tasks', 'posts', 'checks', 'pay', 'figures', 'questions'];

const DEFAULT_BOOK = [
  '🧾 Alle **Rechnungen** des Monats in **TCM Soft** geschrieben',
  '🏦 **Kontoabgleich**: TCM Soft mit Bankeingängen abgeglichen',
  '⏰ **Offene Posten** geprüft, Erinnerungen verschickt',
  '📥 **Eingangsrechnungen** gesammelt (Kräuter, Miete, Material)',
  '💵 **Barzahlungen + Kasse** erfasst',
  '☁️ Belege in **DATEV Unternehmen online** hochgeladen',
  '🔗 **Bankumsätze** in DATEV zugeordnet',
  '❓ **Fragen an Steuerberater** geklärt',
];
const DEFAULT_PAY = [
  '⏱️ **Stunden** aller Mitarbeitenden erfasst',
  '🤒 **Krankheit + Urlaub** eingetragen',
  '📤 Lohndaten an **Steuerberater** gesendet',
  '📄 **Lohnabrechnungen** erhalten + geprüft',
  '💸 **Gehälter** überwiesen',
  '🗂️ Abrechnungen **abgelegt**',
];
const DEFAULT_LINKS = [
  '☁️ DATEV Unternehmen online | https://duo.datev.de',
  '📸 Instagram | https://www.instagram.com',
  '👍 Meta Business Suite | https://business.facebook.com',
  '📍 Google Unternehmensprofil | https://business.google.com',
];

const CATS = {
  book: '📒 Buchhaltung', pay: '💶 Lohn', social: '📣 Social', praxis: '🏥 Praxis', misc: '📌 Sonstiges',
};
const REPEATS = {
  none: 'Einmalig', weekly: 'Wöchentlich', monthly: 'Monatlich', quarterly: 'Vierteljährlich', yearly: 'Jährlich',
};
const STATUS = {
  idee: { emoji: '💡', label: 'Idee' },
  entwurf: { emoji: '✍️', label: 'Entwurf' },
  geplant: { emoji: '📅', label: 'Geplant' },
  live: { emoji: '✅', label: 'Live' },
};
const STATUS_ORDER = ['idee', 'entwurf', 'geplant', 'live'];
const CHANNELS = {
  ig: '📸 Instagram', fb: '👍 Facebook', google: '📍 Google', web: '🌐 Website', mail: '✉️ Newsletter',
};
const HWG = [
  'Keine **Heil- oder Wirkversprechen** ("heilt", "garantiert")',
  'Keine **Angst machenden** oder reißerischen Aussagen',
  '**Foto-Einwilligung** aller gezeigten Personen vorhanden',
];
const JOBS = ['Minijob', 'Teilzeit', 'Vollzeit', 'Azubi', 'Freiberuflich', 'Inhaberin'];

const SEASONS = {
  spring: { emoji: '🌱', name: 'Frühling', phase: 'Holz', organ: 'Leber + Gallenblase', ideas: [
    'Frühjahrsmüdigkeit aus Sicht der TCM', 'Saure Frühlingsküche: Rezept mit Zitrone und Kräutern',
    'Dehnübung für den Leber-Meridian zum Mitmachen'] },
  summer: { emoji: '☀️', name: 'Sommer', phase: 'Feuer', organ: 'Herz + Dünndarm', ideas: [
    'Kühlende Lebensmittel für heiße Tage', 'Rezept: Mungbohnen-Suppe zum Abkühlen',
    'Ruhige Atemübung für Sommerabende'] },
  late: { emoji: '🌾', name: 'Spätsommer', phase: 'Erde', organ: 'Milz + Magen', ideas: [
    'Die Mitte stärken: Milz und Magen in der TCM', 'Rezept: Hirse-Kürbis-Brei',
    'Achtsam essen: 3 Tipps aus der TCM'] },
  autumn: { emoji: '🍂', name: 'Herbst', phase: 'Metall', organ: 'Lunge + Dickdarm', ideas: [
    'Warum die Lunge im Herbst Aufmerksamkeit bekommt', 'Birnen-Rezept für trockene Herbsttage',
    'Qi Gong Übung für tiefes Atmen'] },
  winter: { emoji: '❄️', name: 'Winter', phase: 'Wasser', organ: 'Niere + Blase', ideas: [
    'Ruhe und Rückzug: der Winter in der TCM', 'Wärmende Suppe mit Ingwer und Zimt',
    'Moxa erklärt: Wärme für kalte Tage'] },
};
const EVERGREEN = [
  '🪡 Akupunktur erklärt: So läuft die erste Sitzung ab',
  '🌿 Kraut im Portrait: Herkunft, Geschmack, Tradition',
  '❓ Häufige Frage: Wie lange dauert eine Behandlung?',
  '👋 Team vorstellen: Wer ist wer bei uns?',
  '🧠 Mythos oder Fakt: Tut Akupunktur weh?',
  '🫖 Tee-Moment: Unser Lieblingstee der Saison',
  '📸 Blick hinter die Kulissen: Kräuterapotheke',
  '📅 Praxis-News: Termine, Urlaub, Neuigkeiten',
  '🧘 30 Sekunden Qi Gong zum Mitmachen',
  '📖 TCM Begriff erklärt: Was ist eigentlich Qi?',
  '💬 Weisheit aus der chinesischen Medizin',
  '🍵 Rezept aus der TCM Küche',
];

const $ = (sel, root = document) => root.querySelector(sel);
const main = $('#main');

let db = load();
let device = loadDevice();
const ui = {
  view: device.view || 'start',
  bookMonth: null,
  payMonth: monthKey(new Date()),
  postFilter: 'alle',
  taskFilter: 'alle',
  showDone: false,
  chartPick: null,
  lastIdea: '',
};
ui.bookMonth = bookFocusMonth();

// ---------- Speicher ----------

function emptyDb() {
  const d = {};
  COLLS.forEach((c) => { d[c] = {}; });
  return d;
}

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY));
    if (raw && typeof raw === 'object') {
      const d = emptyDb();
      COLLS.forEach((c) => { if (raw[c]) d[c] = raw[c]; });
      return d;
    }
  } catch (e) { /* leer starten */ }
  return emptyDb();
}

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(db)); } catch (e) { toast('⚠️ Speichern fehlgeschlagen. Bitte Backup machen.'); }
}

function loadDevice() {
  try { return JSON.parse(localStorage.getItem(DEVICE_KEY)) || {}; } catch (e) { return {}; }
}

function saveDevice() {
  try { localStorage.setItem(DEVICE_KEY, JSON.stringify(device)); } catch (e) { /* egal */ }
}

function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }

function put(coll, rec) {
  // Gleiche Millisekunde wie ein Import darf nicht verlieren
  const prev = db[coll][rec.id];
  rec.updatedAt = Math.max(Date.now(), prev ? prev.updatedAt + 1 : 0);
  db[coll][rec.id] = rec;
  save();
  return rec;
}

function remove(coll, id) { put(coll, { id, deleted: true }); }

function get(coll, id) {
  const r = db[coll][id];
  return r && !r.deleted ? r : null;
}

function list(coll) { return Object.values(db[coll]).filter((r) => !r.deleted); }

function settings() {
  const s = get('meta', 'settings') || {};
  return {
    praxis: s.praxis || 'Sinologikum',
    book: s.book || DEFAULT_BOOK,
    pay: s.pay || DEFAULT_PAY,
    links: s.links || DEFAULT_LINKS,
  };
}

function saveSettings(patch) { put('meta', { ...settings(), ...patch, id: 'settings' }); }

function merge(incoming) {
  let changed = 0;
  COLLS.forEach((c) => {
    const src = incoming[c] || {};
    Object.values(src).forEach((rec) => {
      if (!rec || typeof rec.id !== 'string' || typeof rec.updatedAt !== 'number') return;
      const cur = db[c][rec.id];
      if (!cur || rec.updatedAt > cur.updatedAt) { db[c][rec.id] = rec; changed++; }
    });
  });
  save();
  return changed;
}

// ---------- Datum + Format ----------

function pad(n) { return String(n).padStart(2, '0'); }
function dateStr(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
function today() { return dateStr(new Date()); }
function parseDate(s) { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); }
function monthKey(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`; }
function addMonths(key, n) {
  const [y, m] = key.split('-').map(Number);
  return monthKey(new Date(y, m - 1 + n, 1));
}
function monthLabel(key, short) {
  const [y, m] = key.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString('de-DE', short ? { month: 'short' } : { month: 'long', year: 'numeric' });
}
function fmtDate(s) {
  return parseDate(s).toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' });
}
function daysUntil(s) { return Math.round((parseDate(s) - parseDate(today())) / 86400000); }
function relDay(s) {
  const n = daysUntil(s);
  if (n < -1) return `seit ${-n} Tagen fällig`;
  if (n === -1) return 'seit gestern fällig';
  if (n === 0) return 'heute';
  if (n === 1) return 'morgen';
  if (n < 7) return `in ${n} Tagen`;
  return fmtDate(s);
}
function addDays(s, n) { const d = parseDate(s); d.setDate(d.getDate() + n); return dateStr(d); }
function addMonthsToDate(s, n) {
  const d = parseDate(s);
  const day = d.getDate();
  const t = new Date(d.getFullYear(), d.getMonth() + n, 1);
  const last = new Date(t.getFullYear(), t.getMonth() + 1, 0).getDate();
  t.setDate(Math.min(day, last));
  return dateStr(t);
}
function nextDue(s, repeat) {
  if (repeat === 'weekly') return addDays(s, 7);
  if (repeat === 'monthly') return addMonthsToDate(s, 1);
  if (repeat === 'quarterly') return addMonthsToDate(s, 3);
  if (repeat === 'yearly') return addMonthsToDate(s, 12);
  return null;
}
function nextDayOfMonth(day) {
  const d = new Date();
  if (d.getDate() > day) d.setMonth(d.getMonth() + 1, 1);
  d.setDate(day);
  return dateStr(d);
}

const euroFmt = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
function euro(n) { return euroFmt.format(n || 0); }

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
// **fett** wird zu <b>fett</b>, alles andere bleibt Text
function md(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>'); }
function plain(s) { return String(s).replace(/\*\*/g, ''); }

function hash(s) {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

function person(id) { return id ? get('team', id) : null; }
function personTag(id) {
  const p = person(id);
  return p ? `${esc(p.emoji || '🙂')} ${esc(p.name)}` : '';
}
function me() { return person(device.me); }
function standalone() {
  return navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches;
}

function season(d = new Date()) {
  const m = d.getMonth() + 1;
  if (m >= 3 && m <= 5) return SEASONS.spring;
  if (m === 6 || m === 7) return SEASONS.summer;
  if (m === 8) return SEASONS.late;
  if (m >= 9 && m <= 11) return SEASONS.autumn;
  return SEASONS.winter;
}

// ---------- Checklisten ----------

function checkId(kind, month, label) { return `${kind}:${month}:${hash(label)}`; }

function checklist(kind, month) {
  const items = settings()[kind];
  return items.map((label) => {
    const id = checkId(kind, month, label);
    const rec = get('checks', id);
    return { id, label, done: !!(rec && rec.done), by: rec && rec.by, at: rec && rec.updatedAt };
  });
}

function progress(kind, month) {
  const items = checklist(kind, month);
  const done = items.filter((i) => i.done).length;
  return { done, total: items.length, next: items.find((i) => !i.done) };
}

function bookFocusMonth() {
  const prev = addMonths(monthKey(new Date()), -1);
  const p = progress('book', prev);
  return p.done < p.total ? prev : monthKey(new Date());
}

function toggleCheck(id) {
  const rec = get('checks', id);
  const done = !(rec && rec.done);
  put('checks', { id, done, by: device.me || null });
  return done;
}

// ---------- Aufgaben ----------

function openTasks() {
  return list('tasks').filter((t) => !t.done).sort((a, b) => {
    if (a.due && b.due) return a.due.localeCompare(b.due);
    if (a.due) return -1;
    if (b.due) return 1;
    return (b.createdAt || 0) - (a.createdAt || 0);
  });
}

function completeTask(id) {
  const t = get('tasks', id);
  if (!t) return;
  put('tasks', { ...t, done: true, doneAt: Date.now(), doneBy: device.me || null });
  if (t.repeat && t.repeat !== 'none' && t.due) {
    const due = nextDue(t.due, t.repeat);
    put('tasks', { ...t, id: uid(), done: false, doneAt: null, doneBy: null, due, createdAt: Date.now() });
    toast(`🔁 Erledigt! Nächster Termin: <b>${fmtDate(due)}</b>`);
  } else {
    toast('🎉 <b>Erledigt!</b> Gut gemacht.');
  }
}

function seed() {
  if (get('meta', 'seeded')) return;
  const q = ['03-10', '06-10', '09-10', '12-10'].map((md2) => `${new Date().getFullYear()}-${md2}`)
    .find((d) => daysUntil(d) >= 0) || `${new Date().getFullYear() + 1}-03-10`;
  const friday = addDays(today(), (5 - new Date().getDay() + 7) % 7);
  const tasks = [
    { title: 'Belege vom Vormonat in DATEV hochladen', cat: 'book', repeat: 'monthly', due: nextDayOfMonth(5) },
    { title: 'Kontoabgleich TCM Soft mit Bankeingängen', cat: 'book', repeat: 'monthly', due: nextDayOfMonth(5) },
    { title: 'Lohndaten an Steuerberater senden', cat: 'pay', repeat: 'monthly', due: nextDayOfMonth(20) },
    { title: 'Einkommensteuer-Vorauszahlung prüfen', cat: 'book', repeat: 'quarterly', due: q },
    { title: 'Social Media: Posts für nächste Woche planen', cat: 'social', repeat: 'weekly', due: friday },
  ];
  // Feste IDs + uralter Zeitstempel: Startaufgaben verdoppeln sich beim Import nicht
  // und überschreiben nie echte Änderungen aus dem Team
  tasks.forEach((t, i) => {
    db.tasks[`seed-${i}`] = { id: `seed-${i}`, createdAt: 1, updatedAt: 1, who: null, notes: '', done: false, ...t };
  });
  db.meta.seeded = { id: 'seeded', updatedAt: 1 };
  save();
}

// ---------- Bausteine ----------

function bar(done, total) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  return `<div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="${total}" aria-valuenow="${done}"><span style="width:${pct}%"></span></div>`;
}

function monthSwitch(act, key) {
  return `<div class="month-switch">
    <button type="button" class="icon-btn" data-act="${act}" data-step="-1" aria-label="Vorheriger Monat">◀</button>
    <strong>${esc(monthLabel(key))}</strong>
    <button type="button" class="icon-btn" data-act="${act}" data-step="1" aria-label="Nächster Monat">▶</button>
  </div>`;
}

function checkRows(kind, month) {
  return `<ul class="checks">${checklist(kind, month).map((i) => `
    <li><button type="button" class="check ${i.done ? 'done' : ''}" data-act="check" data-id="${esc(i.id)}" data-kind="${kind}" data-month="${month}" aria-pressed="${i.done}">
      <span class="box" aria-hidden="true">${i.done ? '✓' : ''}</span>
      <span class="txt">${md(i.label)}${i.done ? `<small>${i.by ? personTag(i.by) + ' · ' : ''}${new Date(i.at).toLocaleDateString('de-DE')}</small>` : ''}</span>
    </button></li>`).join('')}</ul>`;
}

function linksRow() {
  const links = settings().links.map((l) => {
    const [label, url] = l.split('|').map((s) => s.trim());
    return url && /^https?:\/\//i.test(url) ? { label, url } : null;
  }).filter(Boolean);
  if (!links.length) return '<p class="muted">🔗 Noch keine Links. Unter <b>Einstellungen</b> eintragen.</p>';
  return `<div class="links">${links.map((l) => `<a class="chip link" href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)}</a>`).join('')}</div>`;
}

function taskRow(t) {
  const n = t.due ? daysUntil(t.due) : null;
  const cls = n !== null && n < 0 ? 'late' : n === 0 ? 'now' : '';
  return `<li class="task ${t.done ? 'is-done' : ''}">
    <button type="button" class="round ${t.done ? 'done' : ''}" data-act="${t.done ? 'undo-task' : 'done-task'}" data-id="${t.id}" aria-label="${t.done ? 'Wieder öffnen' : 'Erledigt'}">${t.done ? '✓' : ''}</button>
    <button type="button" class="task-main" data-act="edit-task" data-id="${t.id}">
      <span class="title">${esc(t.title)}</span>
      <span class="meta">
        ${t.due ? `<span class="due ${cls}">${n !== null && n < 0 ? '🔴' : '🗓️'} ${esc(relDay(t.due))}</span>` : ''}
        ${t.cat ? `<span>${esc(CATS[t.cat] || '')}</span>` : ''}
        ${t.who ? `<span>${personTag(t.who)}</span>` : ''}
        ${t.repeat && t.repeat !== 'none' ? `<span>🔁 ${esc(REPEATS[t.repeat])}</span>` : ''}
      </span>
    </button>
  </li>`;
}

function postCard(p) {
  const s = STATUS[p.status] || STATUS.idee;
  const hwgOk = HWG.every((_, i) => p.hwg && p.hwg[i]);
  const warn = !hwgOk && (p.status === 'geplant' || p.status === 'live');
  const nextStatus = STATUS_ORDER[STATUS_ORDER.indexOf(p.status) + 1];
  return `<li class="post">
    <button type="button" class="post-main" data-act="edit-post" data-id="${p.id}">
      <span class="title">${s.emoji} ${esc(p.title || 'Ohne Titel')}</span>
      <span class="meta">
        ${p.date ? `<span>🗓️ ${esc(fmtDate(p.date))}</span>` : ''}
        ${(p.channels || []).map((c) => `<span>${esc(CHANNELS[c] || '')}</span>`).join('')}
        ${p.who ? `<span>${personTag(p.who)}</span>` : ''}
        ${warn ? '<span class="warn">⚠️ HWG-Check offen</span>' : ''}
      </span>
    </button>
    ${nextStatus ? `<button type="button" class="chip" data-act="advance-post" data-id="${p.id}">➡️ ${STATUS[nextStatus].label}</button>` : ''}
  </li>`;
}

// ---------- Diagramm (Umsatz + Ausgaben, 6 Monate) ----------

function chart(endKey) {
  const keys = [];
  for (let i = 5; i >= 0; i--) keys.push(addMonths(endKey, -i));
  const rows = keys.map((k) => {
    const f = get('figures', k) || {};
    return { k, u: Number(f.umsatz) || 0, a: Number(f.ausgaben) || 0 };
  });
  if (!rows.some((r) => r.u || r.a)) {
    return '<p class="muted">📈 Trage unter <b>Buchhaltung</b> Umsatz + Ausgaben ein, dann erscheint hier dein Verlauf.</p>';
  }
  const W = 320, H = 150, top = 8, bottom = 22, left = 4;
  const max = Math.max(...rows.map((r) => Math.max(r.u, r.a))) || 1;
  const plotH = H - top - bottom;
  const gw = (W - left) / rows.length;
  const bw = Math.min(16, (gw - 14) / 2);
  const y = (v) => top + plotH - (v / max) * plotH;
  const barPath = (x, v) => {
    const h = (v / max) * plotH;
    if (h <= 0) return '';
    const r = Math.min(4, bw / 2, h);
    const yt = top + plotH - h;
    const yb = top + plotH;
    return `M${x},${yb}V${yt + r}Q${x},${yt} ${x + r},${yt}H${x + bw - r}Q${x + bw},${yt} ${x + bw},${yt + r}V${yb}Z`;
  };
  const grid = [0.5, 1].map((f) => `<line class="gridline" x1="0" x2="${W}" y1="${y(max * f)}" y2="${y(max * f)}"/>`).join('');
  const groups = rows.map((r, i) => {
    const cx = left + gw * i + gw / 2;
    const x1 = cx - bw - 1;
    const x2 = cx + 1;
    const picked = ui.chartPick === r.k ? ' picked' : '';
    return `<g class="grp${picked}">
      <path class="s1" d="${barPath(x1, r.u)}"/><path class="s2" d="${barPath(x2, r.a)}"/>
      <text class="axis" x="${cx}" y="${H - 6}" text-anchor="middle">${esc(monthLabel(r.k, true))}</text>
      <rect class="hit" x="${left + gw * i}" y="0" width="${gw}" height="${H}" data-act="chart-pick" data-k="${r.k}">
        <title>${esc(monthLabel(r.k))}: Umsatz ${euro(r.u)}, Ausgaben ${euro(r.a)}</title></rect>
    </g>`;
  }).join('');
  const pick = rows.find((r) => r.k === ui.chartPick) || rows[rows.length - 1];
  const diff = pick.u - pick.a;
  return `<div class="viz">
    <p class="hero"><span class="muted">${esc(monthLabel(pick.k))}</span><br><b>${diff >= 0 ? '+' : ''}${euro(diff)}</b> <span class="muted">Ergebnis</span></p>
    <div class="legend"><span><i class="sw s1"></i>Umsatz <b>${euro(pick.u)}</b></span><span><i class="sw s2"></i>Ausgaben <b>${euro(pick.a)}</b></span></div>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Umsatz und Ausgaben der letzten 6 Monate">${grid}<line class="base" x1="0" x2="${W}" y1="${top + plotH}" y2="${top + plotH}"/>${groups}</svg>
    <p class="hint">👆 Monat antippen für Details</p>
    <details><summary>Tabelle anzeigen</summary><table>
      <tr><th>Monat</th><th>Umsatz</th><th>Ausgaben</th><th>Ergebnis</th></tr>
      ${rows.map((r) => `<tr><td>${esc(monthLabel(r.k, true))}</td><td>${euro(r.u)}</td><td>${euro(r.a)}</td><td>${euro(r.u - r.a)}</td></tr>`).join('')}
    </table></details>
  </div>`;
}

// ---------- Ansichten ----------

function nextAction() {
  const open = openTasks();
  const late = open.find((t) => t.due && daysUntil(t.due) <= 0);
  if (late) return { kind: 'task', t: late };
  const p = progress('book', ui.bookMonth);
  if (p.next) return { kind: 'book', item: p.next, month: ui.bookMonth };
  const soon = open.find((t) => t.due);
  return soon ? { kind: 'task', t: soon } : null;
}

const views = {
  start() {
    const m = me();
    const hour = new Date().getHours();
    const hello = hour < 11 ? 'Guten Morgen' : hour < 17 ? 'Hallo' : 'Guten Abend';
    const b = progress('book', ui.bookMonth);
    const pay = progress('pay', ui.payMonth);
    const open = openTasks();
    const lateCount = open.filter((t) => t.due && daysUntil(t.due) < 0).length;
    const week = list('posts').filter((p) => p.status === 'geplant' && p.date && daysUntil(p.date) >= 0 && daysUntil(p.date) < 7)
      .sort((a, b2) => a.date.localeCompare(b2.date));
    const counts = STATUS_ORDER.map((s) => `<span class="chip static">${STATUS[s].emoji} ${list('posts').filter((p) => p.status === s).length}</span>`).join('');
    const na = nextAction();
    const lastExport = device.lastExport ? Math.floor((Date.now() - device.lastExport) / 86400000) : null;
    const needBackup = list('tasks').length > 0 && (lastExport === null || lastExport >= 7);
    const team = list('team');
    const onboarding = !team.length || !m;

    return `
      <header class="top">
        <h1>👋 <b>${hello}${m ? `, ${esc(m.name)}` : ''}</b></h1>
        <p class="lead">${esc(new Date().toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' }))} · ${esc(settings().praxis)}</p>
      </header>

      ${onboarding ? `<section class="card onboarding">
        <h2>🚀 <b>Erste Schritte</b> (ca. 5 Min)</h2>
        <ol>
          <li>${team.length ? '✅' : '⬜'} <b>Team</b> anlegen</li>
          <li>${m ? '✅' : '⬜'} Festlegen, <b>wer dieses Gerät</b> nutzt</li>
          <li>${standalone() ? '✅' : '⬜'} App über <b>Teilen → Zum Home-Bildschirm</b> installieren</li>
        </ol>
        <button type="button" class="btn primary" data-go="settings">Los geht's ➡️</button>
      </section>` : ''}

      ${na ? `<section class="card focus">
        <p class="kicker">🎯 Jetzt dran</p>
        ${na.kind === 'task'
          ? `<p class="focus-title">${esc(na.t.title)}</p><p class="muted">${na.t.due ? esc(relDay(na.t.due)) : ''}</p>
             <button type="button" class="btn primary" data-act="done-task" data-id="${na.t.id}">✅ Erledigt</button>`
          : `<p class="focus-title">${md(na.item.label)}</p><p class="muted">Buchhaltung ${esc(monthLabel(na.month))}</p>
             <button type="button" class="btn primary" data-act="check" data-id="${esc(na.item.id)}" data-kind="book" data-month="${na.month}">✅ Erledigt</button>`}
      </section>` : ''}

      ${needBackup ? `<section class="card nudge">
        <p>💾 <b>Backup fällig</b> ${lastExport === null ? '(noch nie gemacht)' : `(vor ${lastExport} Tagen)`}. Dauert <b>1 Min</b>.</p>
        <button type="button" class="btn ghost" data-act="export">💾 Jetzt sichern</button>
      </section>` : ''}

      <div class="grid">
        <section class="card">
          <h2>📒 <b>Buchhaltung</b> ${esc(monthLabel(ui.bookMonth))}</h2>
          ${bar(b.done, b.total)}
          <p class="muted"><b>${b.done} von ${b.total}</b> erledigt</p>
          ${b.next ? `<p>👉 ${md(b.next.label)}</p>` : '<p>🎉 <b>Monat komplett!</b></p>'}
          <button type="button" class="btn ghost" data-go="book">Öffnen ➡️</button>
        </section>

        <section class="card">
          <h2>💶 <b>Lohn</b> ${esc(monthLabel(ui.payMonth))}</h2>
          ${bar(pay.done, pay.total)}
          <p class="muted"><b>${pay.done} von ${pay.total}</b> erledigt</p>
          ${pay.next ? `<p>👉 ${md(pay.next.label)}</p>` : '<p>🎉 <b>Lohn erledigt!</b></p>'}
          <button type="button" class="btn ghost" data-go="pay">Öffnen ➡️</button>
        </section>

        <section class="card">
          <h2>✅ <b>Fristen</b> ${lateCount ? `<span class="badge">${lateCount} überfällig</span>` : ''}</h2>
          ${open.length ? `<ul class="tasks compact">${open.slice(0, 4).map(taskRow).join('')}</ul>` : '<p class="muted">🌿 Nichts offen.</p>'}
          <button type="button" class="btn ghost" data-go="tasks">Alle Aufgaben ➡️</button>
        </section>

        <section class="card">
          <h2>📣 <b>Social Media</b> diese Woche</h2>
          <div class="chips">${counts}</div>
          ${week.length ? `<ul class="mini">${week.slice(0, 3).map((p) => `<li>🗓️ <b>${esc(fmtDate(p.date))}</b> ${esc(p.title)}</li>`).join('')}</ul>` : '<p class="muted">Noch nichts geplant für die nächsten 7 Tage.</p>'}
          <button type="button" class="btn ghost" data-go="social">Planen ➡️</button>
        </section>

        <section class="card">
          <h2>📈 <b>Zahlen</b></h2>
          ${chart(ui.bookMonth)}
        </section>

        <section class="card">
          <h2>🔗 <b>Schnellzugriff</b></h2>
          ${linksRow()}
        </section>
      </div>`;
  },

  book() {
    const k = ui.bookMonth;
    const p = progress('book', k);
    const f = get('figures', k) || {};
    const qs = list('questions').sort((a, b) => (a.done - b.done) || (b.createdAt - a.createdAt));
    const openQ = qs.filter((q) => !q.done);
    const doneQ = qs.filter((q) => q.done).slice(0, 10);
    return `
      <header class="top"><h1>📒 <b>Buchhaltung</b></h1>${monthSwitch('book-month', k)}</header>
      <section class="card">
        ${bar(p.done, p.total)}
        <p class="muted"><b>${p.done} von ${p.total}</b> erledigt ${p.done === p.total ? '· 🎉 <b>Monat abgeschlossen!</b>' : ''}</p>
        ${checkRows('book', k)}
      </section>
      <div class="grid">
        <section class="card">
          <h2>💰 <b>Zahlen</b> ${esc(monthLabel(k))}</h2>
          <label class="block"><span class="label">Umsatz laut <b>TCM Soft</b> (€)</span>
            <input type="number" inputmode="decimal" min="0" step="1" data-field="umsatz" data-k="${k}" value="${esc(f.umsatz ?? '')}" placeholder="z. B. 12500"></label>
          <label class="block"><span class="label"><b>Ausgaben</b> (€)</span>
            <input type="number" inputmode="decimal" min="0" step="1" data-field="ausgaben" data-k="${k}" value="${esc(f.ausgaben ?? '')}" placeholder="z. B. 8200"></label>
          <p class="hint">💡 Grobe Zahlen reichen. Genaue Werte macht der Steuerberater.</p>
        </section>
        <section class="card">
          <h2>❓ <b>Fragen an Steuerberater</b></h2>
          <form class="quick" data-form="question" autocomplete="off">
            <input name="text" maxlength="200" placeholder="Frage notieren, Enter drücken" enterkeyhint="done">
            <button type="submit" class="icon-btn" aria-label="Frage hinzufügen">➕</button>
          </form>
          ${openQ.length ? `<ul class="qlist">${openQ.map((q) => `<li>
            <button type="button" class="round" data-act="q-done" data-id="${q.id}" aria-label="Geklärt">✓</button>
            <span>${esc(q.text)}</span>
            <button type="button" class="icon-btn small" data-act="q-del" data-id="${q.id}" aria-label="Löschen">🗑️</button></li>`).join('')}</ul>`
            : '<p class="muted">✨ Keine offenen Fragen.</p>'}
          ${openQ.length ? '<button type="button" class="btn ghost" data-act="q-copy">📋 Alle offenen Fragen kopieren</button>' : ''}
          ${doneQ.length ? `<details><summary>✅ Geklärt (${doneQ.length})</summary><ul class="qlist done">${doneQ.map((q) => `<li>
            <button type="button" class="round done" data-act="q-undo" data-id="${q.id}" aria-label="Wieder öffnen">✓</button><span>${esc(q.text)}</span></li>`).join('')}</ul></details>` : ''}
        </section>
        <section class="card">
          <h2>🔗 <b>Schnellzugriff</b></h2>
          ${linksRow()}
        </section>
      </div>`;
  },

  pay() {
    const k = ui.payMonth;
    const p = progress('pay', k);
    const staff = list('team').filter((t) => t.inPayroll !== false && t.job !== 'Inhaberin')
      .sort((a, b) => a.name.localeCompare(b.name));
    return `
      <header class="top"><h1>💶 <b>Lohn</b></h1>${monthSwitch('pay-month', k)}</header>
      <section class="card">
        ${bar(p.done, p.total)}
        <p class="muted"><b>${p.done} von ${p.total}</b> erledigt ${p.done === p.total ? '· 🎉 <b>Lohn erledigt!</b>' : ''}</p>
        ${checkRows('pay', k)}
      </section>
      <section class="card">
        <h2>👥 <b>Mitarbeitende</b> ${esc(monthLabel(k))}</h2>
        ${staff.length ? `<div class="staff">${staff.map((s) => {
          const r = get('pay', `${k}:${s.id}`) || {};
          return `<div class="staff-row">
            <p class="name">${esc(s.emoji || '🙂')} <b>${esc(s.name)}</b> <span class="muted">${esc(s.job || '')}${s.hours ? ` · Soll ${esc(s.hours)} Std` : ''}</span></p>
            <div class="nums">
              <label><span>⏱️ Std</span><input type="number" inputmode="decimal" min="0" step="0.25" data-pay="hours" data-k="${k}" data-p="${s.id}" value="${esc(r.hours ?? '')}"></label>
              <label><span>🏖️ Urlaub</span><input type="number" inputmode="decimal" min="0" step="0.5" data-pay="vacation" data-k="${k}" data-p="${s.id}" value="${esc(r.vacation ?? '')}"></label>
              <label><span>🤒 Krank</span><input type="number" inputmode="decimal" min="0" step="0.5" data-pay="sick" data-k="${k}" data-p="${s.id}" value="${esc(r.sick ?? '')}"></label>
            </div>
            <input class="note" maxlength="200" placeholder="Notiz (z. B. Bonus, neue Bankverbindung)" data-pay="note" data-k="${k}" data-p="${s.id}" value="${esc(r.note ?? '')}">
          </div>`;
        }).join('')}</div>
        <button type="button" class="btn primary" data-act="pay-copy">📋 Lohndaten für Steuerberater kopieren</button>
        <p class="hint">💡 Kopiert eine fertige Übersicht. In E-Mail oder DATEV einfügen.</p>`
        : '<p class="muted">👥 Noch keine Mitarbeitenden. Unter <b>Einstellungen → Team</b> anlegen (2 Min).</p><button type="button" class="btn ghost" data-go="settings">Team anlegen ➡️</button>'}
      </section>`;
  },

  social() {
    const s = season();
    const posts = list('posts');
    const f = ui.postFilter;
    const sortPosts = (arr, st) => arr.sort((a, b) => {
      if (st === 'geplant') return (a.date || '9').localeCompare(b.date || '9');
      if (st === 'live') return (b.date || '').localeCompare(a.date || '');
      return (b.createdAt || 0) - (a.createdAt || 0);
    });
    const order = ['geplant', 'entwurf', 'idee', 'live'];
    const sections = (f === 'alle' ? order : [f]).map((st) => {
      let arr = sortPosts(posts.filter((p) => p.status === st), st);
      if (st === 'live' && f === 'alle') arr = arr.slice(0, 5);
      if (!arr.length) return '';
      return `<h3>${STATUS[st].emoji} ${STATUS[st].label}</h3><ul class="posts">${arr.map(postCard).join('')}</ul>`;
    }).join('');
    return `
      <header class="top"><h1>📣 <b>Social Media</b></h1></header>
      <div class="row">
        <button type="button" class="btn primary" data-act="new-post">➕ Neuer Post</button>
        <button type="button" class="btn ghost" data-act="idea">🎲 Idee ziehen</button>
      </div>
      <section class="card season">
        <p class="kicker">${s.emoji} Jetzt: ${s.name}</p>
        <p>In der TCM: Phase <b>${s.phase}</b>, Organe <b>${s.organ}</b>.</p>
        <ul class="mini">${s.ideas.map((i) => `<li><button type="button" class="link-btn" data-act="idea-save" data-text="${esc(i)}">💡 ${esc(i)}</button></li>`).join('')}</ul>
        <p class="hint">👆 Antippen = als Idee speichern</p>
      </section>
      <div class="chips filter">
        <button type="button" class="chip ${f === 'alle' ? 'on' : ''}" data-act="post-filter" data-f="alle">Alle (${posts.length})</button>
        ${STATUS_ORDER.map((st) => `<button type="button" class="chip ${f === st ? 'on' : ''}" data-act="post-filter" data-f="${st}">${STATUS[st].emoji} ${STATUS[st].label} (${posts.filter((p) => p.status === st).length})</button>`).join('')}
      </div>
      ${sections || '<p class="muted empty">✨ Noch keine Posts hier. Tipp: <b>🎲 Idee ziehen</b></p>'}
      <section class="card hwg">
        <h2>⚖️ <b>Heilmittelwerbegesetz</b> kurz</h2>
        <ul class="mini">${HWG.map((h) => `<li>${md(h)}</li>`).join('')}</ul>
        <p class="hint">Im Zweifel vor dem Posten kurz prüfen lassen.</p>
      </section>`;
  },

  tasks() {
    const mine = ui.taskFilter === 'meine';
    const all = list('tasks').filter((t) => !mine || !t.who || t.who === device.me);
    const open = all.filter((t) => !t.done);
    const sorted = openTasks().filter((t) => open.includes(t));
    const groups = [
      ['🔴 Überfällig', sorted.filter((t) => t.due && daysUntil(t.due) < 0)],
      ['📍 Heute', sorted.filter((t) => t.due && daysUntil(t.due) === 0)],
      ['📆 Nächste 7 Tage', sorted.filter((t) => t.due && daysUntil(t.due) > 0 && daysUntil(t.due) <= 7)],
      ['🗓️ Später', sorted.filter((t) => t.due && daysUntil(t.due) > 7)],
      ['📥 Ohne Datum', sorted.filter((t) => !t.due)],
    ].filter(([, arr]) => arr.length);
    const done = all.filter((t) => t.done).sort((a, b) => (b.doneAt || 0) - (a.doneAt || 0)).slice(0, 15);
    return `
      <header class="top"><h1>✅ <b>Aufgaben + Fristen</b></h1></header>
      <form class="quick" data-form="task" autocomplete="off">
        <input name="title" maxlength="120" placeholder="Schnell notieren, Enter drücken" enterkeyhint="done">
        <button type="submit" class="icon-btn" aria-label="Aufgabe hinzufügen">➕</button>
      </form>
      <div class="row">
        <button type="button" class="btn ghost" data-act="new-task">📝 Mit Datum + Details</button>
      </div>
      <div class="chips filter">
        <button type="button" class="chip ${!mine ? 'on' : ''}" data-act="task-filter" data-f="alle">👥 Alle</button>
        <button type="button" class="chip ${mine ? 'on' : ''}" data-act="task-filter" data-f="meine">🙋 Nur meine</button>
      </div>
      ${groups.length ? groups.map(([title, arr]) => `<h3>${title} <span class="muted">(${arr.length})</span></h3><ul class="tasks">${arr.map(taskRow).join('')}</ul>`).join('')
        : '<p class="muted empty">🌿 <b>Alles erledigt.</b> Durchatmen.</p>'}
      ${done.length ? `<details class="done-list"><summary>✅ Zuletzt erledigt (${done.length})</summary><ul class="tasks">${done.map(taskRow).join('')}</ul></details>` : ''}`;
  },

  settings() {
    const s = settings();
    const team = list('team').sort((a, b) => a.name.localeCompare(b.name));
    const last = device.lastExport ? new Date(device.lastExport).toLocaleDateString('de-DE') : 'noch nie';
    return `
      <header class="top"><h1>⚙️ <b>Einstellungen</b></h1></header>
      <div class="grid">
        <section class="card">
          <h2>👥 <b>Team</b></h2>
          ${team.length ? `<ul class="team">${team.map((t) => `<li><button type="button" class="task-main" data-act="edit-person" data-id="${t.id}">
            <span class="title">${esc(t.emoji || '🙂')} ${esc(t.name)}</span><span class="meta"><span>${esc(t.job || '')}</span>${t.hours ? `<span>Soll ${esc(t.hours)} Std/Monat</span>` : ''}</span></button></li>`).join('')}</ul>`
            : '<p class="muted">Noch niemand angelegt.</p>'}
          <button type="button" class="btn primary" data-act="new-person">➕ Person hinzufügen</button>
        </section>

        <section class="card">
          <h2>📱 <b>Dieses Gerät</b> gehört</h2>
          <select data-act="set-me" aria-label="Wer nutzt dieses Gerät">
            <option value="">Bitte wählen</option>
            ${team.map((t) => `<option value="${t.id}" ${device.me === t.id ? 'selected' : ''}>${esc(t.emoji || '🙂')} ${esc(t.name)}</option>`).join('')}
          </select>
          <p class="hint">💡 So sieht das Team, <b>wer</b> etwas abgehakt hat.</p>
          <label class="block"><span class="label">🏥 <b>Praxisname</b></span>
            <input data-setting="praxis" maxlength="60" value="${esc(s.praxis)}"></label>
        </section>

        <section class="card">
          <h2>💾 <b>Backup + Team-Austausch</b></h2>
          <p class="muted">Letztes Backup: <b>${esc(last)}</b></p>
          <ol class="steps">
            <li><b>Sichern</b> tippen → "In Dateien sichern" → Ordner <b>iCloud Drive / Praxis</b></li>
            <li>Kollegin oder Kollege tippt <b>Importieren</b> und wählt die Datei</li>
            <li>Fertig: Daten werden <b>zusammengeführt</b>, neueste Änderung gewinnt</li>
          </ol>
          <div class="row">
            <button type="button" class="btn primary" data-act="export">💾 Sichern</button>
            <label class="btn ghost file">📂 Importieren<input type="file" accept="application/json,.json" data-act="import" hidden></label>
          </div>
        </section>

        <section class="card">
          <h2>🔗 <b>Links</b></h2>
          <p class="hint">Eine Zeile pro Link: <b>Name | https://adresse</b></p>
          <textarea data-list="links" rows="5">${esc(s.links.join('\n'))}</textarea>
          <button type="button" class="btn ghost" data-act="save-list" data-list="links">Speichern</button>
        </section>

        <section class="card">
          <h2>📒 <b>Checkliste Buchhaltung</b></h2>
          <p class="hint">Eine Zeile pro Schritt. <b>**fett**</b> für wichtige Wörter.</p>
          <textarea data-list="book" rows="8">${esc(s.book.join('\n'))}</textarea>
          <button type="button" class="btn ghost" data-act="save-list" data-list="book">Speichern</button>
        </section>

        <section class="card">
          <h2>💶 <b>Checkliste Lohn</b></h2>
          <p class="hint">Eine Zeile pro Schritt.</p>
          <textarea data-list="pay" rows="6">${esc(s.pay.join('\n'))}</textarea>
          <button type="button" class="btn ghost" data-act="save-list" data-list="pay">Speichern</button>
        </section>

        <section class="card">
          <h2>🔒 <b>Datenschutz</b></h2>
          <ul class="mini">
            <li>Alle Daten bleiben <b>nur auf diesem Gerät</b>.</li>
            <li><b>Keine Patientendaten</b> eintragen. Die gehören in TCM Soft.</li>
            <li>App über <b>Teilen → Zum Home-Bildschirm</b> installieren, sonst kann Safari Daten nach 7 Tagen löschen.</li>
          </ul>
          <button type="button" class="btn ghost danger" data-act="wipe">🗑️ Alle Daten auf diesem Gerät löschen</button>
        </section>
      </div>`;
  },
};

// ---------- Rendern ----------

function render() {
  main.innerHTML = views[ui.view]();
  document.querySelectorAll('#nav [data-view]').forEach((b) => {
    b.classList.toggle('on', b.dataset.view === ui.view);
    b.setAttribute('aria-current', b.dataset.view === ui.view ? 'page' : 'false');
  });
  $('#brand-name').textContent = settings().praxis;
}

function go(view) {
  ui.view = view;
  device.view = view;
  saveDevice();
  render();
  window.scrollTo(0, 0);
}

let toastTimer;
function toast(html) {
  const t = $('#toast');
  t.innerHTML = html;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 2600);
}

// ---------- Bottom Sheet (Bearbeiten) ----------

let sheetSubmit = null;
function openSheet(html, onSubmit) {
  $('#sheet-card').innerHTML = html;
  $('#sheet').hidden = false;
  sheetSubmit = onSubmit;
  document.body.classList.add('locked');
  const first = $('#sheet-card input:not([type=checkbox]), #sheet-card textarea');
  if (first && !first.value) first.focus();
}
function closeSheet() {
  $('#sheet').hidden = true;
  $('#sheet-card').innerHTML = '';
  sheetSubmit = null;
  document.body.classList.remove('locked');
}

function teamOptions(selected) {
  return `<option value="">👥 Niemand bestimmtes</option>${list('team').map((t) =>
    `<option value="${t.id}" ${selected === t.id ? 'selected' : ''}>${esc(t.emoji || '🙂')} ${esc(t.name)}</option>`).join('')}`;
}

function taskSheet(t) {
  const isNew = !t;
  t = t || { title: '', due: '', cat: 'praxis', who: device.me || '', repeat: 'none', notes: '' };
  openSheet(`
    <form data-form="sheet" autocomplete="off">
      <div class="sheet-head"><h2>${isNew ? '📝 <b>Neue Aufgabe</b>' : '✏️ <b>Aufgabe</b>'}</h2>
        <button type="button" class="icon-btn" data-act="close-sheet" aria-label="Schließen">✕</button></div>
      <label class="block"><span class="label"><b>Was</b> ist zu tun?</span><input name="title" maxlength="120" required value="${esc(t.title)}"></label>
      <div class="two">
        <label class="block"><span class="label">🗓️ <b>Fällig</b></span><input type="date" name="due" value="${esc(t.due || '')}"></label>
        <label class="block"><span class="label">🔁 <b>Wiederholen</b></span><select name="repeat">${Object.entries(REPEATS).map(([k, v]) => `<option value="${k}" ${t.repeat === k ? 'selected' : ''}>${v}</option>`).join('')}</select></label>
      </div>
      <div class="two">
        <label class="block"><span class="label">🗂️ <b>Bereich</b></span><select name="cat">${Object.entries(CATS).map(([k, v]) => `<option value="${k}" ${t.cat === k ? 'selected' : ''}>${v}</option>`).join('')}</select></label>
        <label class="block"><span class="label">🙋 <b>Wer</b></span><select name="who">${teamOptions(t.who)}</select></label>
      </div>
      <label class="block"><span class="label">📎 Notiz</span><textarea name="notes" rows="3" maxlength="1000">${esc(t.notes || '')}</textarea></label>
      <div class="row">
        ${isNew ? '' : '<button type="button" class="btn ghost danger" data-act="sheet-delete">🗑️ Löschen</button>'}
        <button type="submit" class="btn primary">Speichern ✅</button>
      </div>
    </form>`, (fd, action) => {
    if (action === 'delete') { remove('tasks', t.id); toast('🗑️ Gelöscht'); return; }
    const rec = {
      ...(isNew ? { id: uid(), createdAt: Date.now(), done: false } : t),
      title: fd.get('title').trim(), due: fd.get('due') || null, repeat: fd.get('repeat'),
      cat: fd.get('cat'), who: fd.get('who') || null, notes: fd.get('notes').trim(),
    };
    put('tasks', rec);
    toast(isNew ? '📝 <b>Aufgabe angelegt</b>' : '💾 Gespeichert');
  });
}

function postSheet(p, presetTitle) {
  const isNew = !p;
  p = p || { title: presetTitle || '', status: 'idee', channels: ['ig'], date: '', text: '', notes: '', who: device.me || '', hwg: {} };
  openSheet(`
    <form data-form="sheet" autocomplete="off">
      <div class="sheet-head"><h2>${isNew ? '➕ <b>Neuer Post</b>' : '✏️ <b>Post</b>'}</h2>
        <button type="button" class="icon-btn" data-act="close-sheet" aria-label="Schließen">✕</button></div>
      <label class="block"><span class="label"><b>Thema</b></span><input name="title" maxlength="120" required value="${esc(p.title)}"></label>
      <fieldset class="block"><legend class="label"><b>Status</b></legend><div class="chips">
        ${STATUS_ORDER.map((s) => `<label class="chip pick"><input type="radio" name="status" value="${s}" ${p.status === s ? 'checked' : ''}><span>${STATUS[s].emoji} ${STATUS[s].label}</span></label>`).join('')}
      </div></fieldset>
      <fieldset class="block"><legend class="label"><b>Kanäle</b></legend><div class="chips">
        ${Object.entries(CHANNELS).map(([k, v]) => `<label class="chip pick"><input type="checkbox" name="channels" value="${k}" ${(p.channels || []).includes(k) ? 'checked' : ''}><span>${v}</span></label>`).join('')}
      </div></fieldset>
      <div class="two">
        <label class="block"><span class="label">🗓️ <b>Datum</b></span><input type="date" name="date" value="${esc(p.date || '')}"></label>
        <label class="block"><span class="label">🙋 <b>Wer</b></span><select name="who">${teamOptions(p.who)}</select></label>
      </div>
      <label class="block"><span class="label">✍️ <b>Text</b> (Caption)</span><textarea name="text" rows="5" maxlength="2200">${esc(p.text || '')}</textarea></label>
      ${p.text ? '<button type="button" class="btn ghost" data-act="copy-caption">📋 Text kopieren</button>' : ''}
      <label class="block"><span class="label">🖼️ Bildidee + Notizen</span><textarea name="notes" rows="2" maxlength="1000">${esc(p.notes || '')}</textarea></label>
      <fieldset class="block"><legend class="label">⚖️ <b>HWG-Check</b> vor dem Posten</legend>
        ${HWG.map((h, i) => `<label class="tick"><input type="checkbox" name="hwg${i}" ${p.hwg && p.hwg[i] ? 'checked' : ''}><span>${md(h)}</span></label>`).join('')}
      </fieldset>
      <div class="row">
        ${isNew ? '' : '<button type="button" class="btn ghost danger" data-act="sheet-delete">🗑️ Löschen</button>'}
        <button type="submit" class="btn primary">Speichern ✅</button>
      </div>
    </form>`, (fd, action) => {
    if (action === 'delete') { remove('posts', p.id); toast('🗑️ Gelöscht'); return; }
    const rec = {
      ...(isNew ? { id: uid(), createdAt: Date.now() } : p),
      title: fd.get('title').trim(), status: fd.get('status') || 'idee', channels: fd.getAll('channels'),
      date: fd.get('date') || null, who: fd.get('who') || null, text: fd.get('text'), notes: fd.get('notes'),
      hwg: { 0: !!fd.get('hwg0'), 1: !!fd.get('hwg1'), 2: !!fd.get('hwg2') },
    };
    put('posts', rec);
    toast(isNew ? '💡 <b>Post angelegt</b>' : '💾 Gespeichert');
  });
}

function personSheet(t) {
  const isNew = !t;
  t = t || { name: '', emoji: '🙂', job: 'Teilzeit', hours: '', inPayroll: true };
  openSheet(`
    <form data-form="sheet" autocomplete="off">
      <div class="sheet-head"><h2>${isNew ? '➕ <b>Neue Person</b>' : '✏️ <b>Person</b>'}</h2>
        <button type="button" class="icon-btn" data-act="close-sheet" aria-label="Schließen">✕</button></div>
      <div class="two narrow">
        <label class="block"><span class="label"><b>Emoji</b></span><input name="emoji" maxlength="4" value="${esc(t.emoji || '')}"></label>
        <label class="block"><span class="label"><b>Name</b></span><input name="name" maxlength="40" required value="${esc(t.name)}"></label>
      </div>
      <div class="two">
        <label class="block"><span class="label">💼 <b>Beschäftigung</b></span><select name="job">${JOBS.map((j) => `<option ${t.job === j ? 'selected' : ''}>${j}</option>`).join('')}</select></label>
        <label class="block"><span class="label">⏱️ <b>Soll-Std/Monat</b></span><input type="number" inputmode="decimal" min="0" step="0.5" name="hours" value="${esc(t.hours ?? '')}"></label>
      </div>
      <label class="tick"><input type="checkbox" name="inPayroll" ${t.inPayroll !== false ? 'checked' : ''}><span>In der <b>Lohnabrechnung</b> anzeigen</span></label>
      <div class="row">
        ${isNew ? '' : '<button type="button" class="btn ghost danger" data-act="sheet-delete">🗑️ Löschen</button>'}
        <button type="submit" class="btn primary">Speichern ✅</button>
      </div>
    </form>`, (fd, action) => {
    if (action === 'delete') {
      remove('team', t.id);
      if (device.me === t.id) { device.me = null; saveDevice(); }
      toast('🗑️ Gelöscht');
      return;
    }
    const rec = {
      ...(isNew ? { id: uid() } : t),
      name: fd.get('name').trim(), emoji: fd.get('emoji').trim() || '🙂', job: fd.get('job'),
      hours: fd.get('hours') || '', inPayroll: !!fd.get('inPayroll'),
    };
    put('team', rec);
    if (isNew && !device.me && list('team').length === 1) { device.me = rec.id; saveDevice(); }
    toast(isNew ? `👋 <b>${esc(rec.name)}</b> ist im Team` : '💾 Gespeichert');
  });
}

function ideaSheet() {
  const s = season();
  const pool = [...s.ideas.map((i) => `${s.emoji} ${i}`), ...EVERGREEN].filter((i) => i !== ui.lastIdea);
  const idea = pool[Math.floor(Math.random() * pool.length)];
  ui.lastIdea = idea;
  openSheet(`
    <div class="sheet-head"><h2>🎲 <b>Deine Idee</b></h2>
      <button type="button" class="icon-btn" data-act="close-sheet" aria-label="Schließen">✕</button></div>
    <p class="idea">${esc(idea)}</p>
    <div class="row">
      <button type="button" class="btn ghost" data-act="idea">🔄 Andere</button>
      <button type="button" class="btn primary" data-act="idea-save" data-text="${esc(idea)}">💡 Speichern</button>
    </div>`, null);
}

// ---------- Kopieren, Backup ----------

async function copy(text, msg) {
  try {
    await navigator.clipboard.writeText(text);
    toast(msg || '📋 <b>Kopiert!</b> Jetzt einfügen.');
  } catch (e) {
    toast('⚠️ Kopieren ging nicht. Bitte Text markieren.');
  }
}

function payText(k) {
  const staff = list('team').filter((t) => t.inPayroll !== false && t.job !== 'Inhaberin').sort((a, b) => a.name.localeCompare(b.name));
  const lines = staff.map((s) => {
    const r = get('pay', `${k}:${s.id}`) || {};
    const num = (v) => (Number(v) || 0).toLocaleString('de-DE');
    const parts = [`${num(r.hours)} Std`, `Urlaub ${num(r.vacation)} Tage`, `Krank ${num(r.sick)} Tage`];
    return `• ${s.name} (${s.job}): ${parts.join(', ')}${r.note ? `. Notiz: ${r.note}` : ''}`;
  });
  return `Lohndaten ${monthLabel(k)} (${settings().praxis})\n\n${lines.join('\n')}\n`;
}

async function exportBackup() {
  const name = `praxis-cockpit-${today()}.json`;
  const json = JSON.stringify({ app: 'praxis-cockpit', version: 1, exportedAt: Date.now(), by: me() ? me().name : null, data: db });
  const file = new File([json], name, { type: 'application/json' });
  try {
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], title: 'Praxis-Cockpit Backup' });
    } else {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(file);
      a.download = name;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    }
    device.lastExport = Date.now();
    saveDevice();
    toast('💾 <b>Backup gesichert!</b>');
    render();
  } catch (e) {
    if (e && e.name === 'AbortError') return;
    toast('⚠️ Backup ging nicht. Bitte nochmal versuchen.');
  }
}

async function importBackup(input) {
  const file = input.files && input.files[0];
  input.value = '';
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    if (!data || data.app !== 'praxis-cockpit' || !data.data) throw new Error('falsche Datei');
    const n = merge(data.data);
    toast(n ? `✅ <b>${n} Einträge</b> übernommen${data.by ? ` von ${esc(data.by)}` : ''}` : '✅ Alles war schon aktuell');
    render();
  } catch (e) {
    toast('⚠️ Das ist keine Praxis-Cockpit Datei.');
  }
}

// ---------- Events ----------

document.addEventListener('click', (e) => {
  const nav = e.target.closest('[data-view]');
  if (nav) { go(nav.dataset.view); return; }
  const goBtn = e.target.closest('[data-go]');
  if (goBtn) { go(goBtn.dataset.go); return; }
  if (e.target.id === 'sheet') { closeSheet(); return; }

  const el = e.target.closest('[data-act]');
  if (!el || el.tagName === 'SELECT' || el.type === 'file') return;
  const { act, id } = el.dataset;

  switch (act) {
    case 'check': {
      const { kind, month } = el.dataset;
      const done = toggleCheck(id);
      const p = progress(kind, month);
      if (done && p.done === p.total) toast(`🎉 <b>${kind === 'book' ? 'Buchhaltung' : 'Lohn'} ${esc(monthLabel(month))} komplett!</b>`);
      else if (done) toast('✅ Abgehakt');
      break;
    }
    case 'book-month': ui.bookMonth = addMonths(ui.bookMonth, Number(el.dataset.step)); break;
    case 'pay-month': ui.payMonth = addMonths(ui.payMonth, Number(el.dataset.step)); break;
    case 'chart-pick': ui.chartPick = el.dataset.k; break;
    case 'done-task': completeTask(id); break;
    case 'undo-task': { const t = get('tasks', id); if (t) put('tasks', { ...t, done: false, doneAt: null }); break; }
    case 'edit-task': taskSheet(get('tasks', id)); return;
    case 'new-task': taskSheet(null); return;
    case 'task-filter': ui.taskFilter = el.dataset.f; break;
    case 'new-post': postSheet(null); return;
    case 'edit-post': postSheet(get('posts', id)); return;
    case 'advance-post': {
      const p = get('posts', id);
      if (!p) break;
      const next = STATUS_ORDER[STATUS_ORDER.indexOf(p.status) + 1];
      if (next === 'geplant' && !p.date) { postSheet({ ...p, status: 'geplant' }); toast('🗓️ Bitte noch ein <b>Datum</b> wählen'); return; }
      put('posts', { ...p, status: next, date: next === 'live' && !p.date ? today() : p.date });
      toast(`${STATUS[next].emoji} Jetzt <b>${STATUS[next].label}</b>`);
      break;
    }
    case 'post-filter': ui.postFilter = el.dataset.f; break;
    case 'idea': ideaSheet(); return;
    case 'idea-save': {
      put('posts', { id: uid(), createdAt: Date.now(), title: el.dataset.text, status: 'idee', channels: ['ig'], date: null, text: '', notes: '', who: device.me || null, hwg: {} });
      closeSheet();
      toast('💡 <b>Idee gespeichert</b>');
      break;
    }
    case 'copy-caption': copy($('#sheet-card [name=text]').value); return;
    case 'q-done': case 'q-undo': {
      const q = get('questions', id);
      if (q) put('questions', { ...q, done: act === 'q-done' });
      break;
    }
    case 'q-del': remove('questions', id); break;
    case 'q-copy': {
      const qs = list('questions').filter((q) => !q.done).map((q) => `• ${q.text}`).join('\n');
      copy(`Fragen an den Steuerberater (${settings().praxis})\n\n${qs}\n`);
      return;
    }
    case 'pay-copy': copy(payText(ui.payMonth), '📋 <b>Lohndaten kopiert!</b> In E-Mail einfügen.'); return;
    case 'new-person': personSheet(null); return;
    case 'edit-person': personSheet(get('team', id)); return;
    case 'save-list': {
      const key = el.dataset.list;
      const lines = $(`textarea[data-list="${key}"]`).value.split('\n').map((l) => l.trim()).filter(Boolean);
      saveSettings({ [key]: lines.length ? lines : null });
      toast('💾 <b>Gespeichert</b>');
      break;
    }
    case 'export': exportBackup(); return;
    case 'wipe': {
      if (!confirm('Wirklich ALLE Daten auf diesem Gerät löschen? Vorher Backup machen!')) return;
      if (!confirm('Letzte Chance: wirklich löschen?')) return;
      localStorage.removeItem(KEY);
      localStorage.removeItem(DEVICE_KEY);
      location.reload();
      return;
    }
    case 'close-sheet': closeSheet(); return;
    case 'sheet-delete': {
      if (!confirm('Wirklich löschen?')) return;
      const fn = sheetSubmit;
      closeSheet();
      if (fn) fn(null, 'delete');
      break;
    }
    default: return;
  }
  render();
});

document.addEventListener('submit', (e) => {
  const form = e.target;
  e.preventDefault();
  const kind = form.dataset.form;
  const fd = new FormData(form);
  if (kind === 'sheet' && sheetSubmit) {
    const fn = sheetSubmit;
    closeSheet();
    fn(fd, 'save');
  } else if (kind === 'task') {
    const title = (fd.get('title') || '').trim();
    if (!title) return;
    put('tasks', { id: uid(), createdAt: Date.now(), title, due: null, cat: 'praxis', who: device.me || null, repeat: 'none', notes: '', done: false });
    toast('📥 <b>Notiert!</b> Datum später setzen.');
  } else if (kind === 'question') {
    const text = (fd.get('text') || '').trim();
    if (!text) return;
    put('questions', { id: uid(), createdAt: Date.now(), text, done: false, by: device.me || null });
  } else {
    return;
  }
  render();
  const again = $(`form[data-form="${kind}"] input`);
  if (again) again.focus();
});

document.addEventListener('change', (e) => {
  const el = e.target;
  if (el.dataset.act === 'set-me') { device.me = el.value || null; saveDevice(); toast('📱 Gespeichert'); render(); return; }
  if (el.dataset.act === 'import') { importBackup(el); return; }
  if (el.dataset.field) {
    const k = el.dataset.k;
    const cur = get('figures', k) || { id: k };
    put('figures', { ...cur, id: k, [el.dataset.field]: el.value === '' ? null : Number(el.value) });
    toast('💾 Gespeichert');
    return;
  }
  if (el.dataset.pay) {
    const id = `${el.dataset.k}:${el.dataset.p}`;
    const cur = get('pay', id) || { id };
    const v = el.dataset.pay === 'note' ? el.value.trim() : (el.value === '' ? null : Number(el.value));
    put('pay', { ...cur, id, [el.dataset.pay]: v });
    return;
  }
  if (el.dataset.setting) { saveSettings({ [el.dataset.setting]: el.value.trim() || null }); render(); }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !$('#sheet').hidden) closeSheet();
});

// Andere Tabs desselben Geräts aktuell halten
window.addEventListener('storage', (e) => { if (e.key === KEY) { db = load(); render(); } });

// ---------- Start ----------

seed();
if (!views[ui.view]) ui.view = 'start';
render();

if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
}
