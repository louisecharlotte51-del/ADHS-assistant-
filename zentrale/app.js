'use strict';
/* Zentrale – UI. Reine Logik steht in logic.js (Global `Logic`). Daten nur lokal. */

const STORE_KEY = 'zentrale-v1';
const AREAS = [
  { id: 'uni', name: 'Uni' },
  { id: 'arbeit', name: 'Arbeit' },
  { id: 'privat', name: 'Privat' },
  { id: 'partei', name: 'Partei' },
  { id: 'adhs', name: 'ADHS-Projekt' },
];
const WORK_DAYS = [0, 3]; // Montag, Donnerstag (Drees & Sommer)
const PRAISE = ['Stark.', 'Geschafft.', 'Ein Ding weniger.', 'Gut gemacht.', 'Das zählt.'];
const DAYNAMES = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
const today = () => new Date().toLocaleDateString('sv');
const pick = (a) => a[Math.floor(Math.random() * a.length)];
// Eigene Namen aus den Einstellungen; IDs und Farben bleiben fest
const areas = () => { const n = getCfg().names || {}; return AREAS.map((a) => ({ ...a, name: n[a.id] || a.name })); };
const area = (id) => areas().find((a) => a.id === id) || areas()[0];
const facts = (arr) => arr.filter(Boolean).map((x) => `<span>${esc(x)}</span>`).join('');
const chip = (id) => `style="--chip:var(--${area(id).id})"`;

/* ---------- Speicher ---------- */

function load() {
  try {
    const s = JSON.parse(localStorage.getItem(STORE_KEY));
    if (s && Array.isArray(s.tasks)) return s;
  } catch (e) { /* leer oder blockiert */ }
  return { tasks: [] };
}
let state = load();
function save() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { toast('Speichern nicht möglich (Privatmodus?)'); }
}
const find = (id) => state.tasks.find((t) => t.id === id);
function touch(t) { t.updatedAt = Date.now(); save(); }

/* ---------- Einstellungen (nur dieses Gerät, nicht im Backup) ---------- */

const CFG_KEY = 'zentrale-cfg-v1';
function getCfg() { try { return JSON.parse(localStorage.getItem(CFG_KEY)) || {}; } catch (e) { return {}; } }
function setCfg(c) { try { localStorage.setItem(CFG_KEY, JSON.stringify(c)); } catch (e) { toast('Speichern nicht möglich'); } }

/* ---------- Apple-Kalender (nur lesen, über den Connector) ---------- */

const CAL_KEY = 'zentrale-cal-v1';
let cal = (() => { try { return JSON.parse(localStorage.getItem(CAL_KEY)) || { at: 0, events: [] }; } catch (e) { return { at: 0, events: [] }; } })();
async function syncCalendar(force) {
  const base = getCfg().splitUrl;
  if (!base || (!force && Date.now() - cal.at < 15 * 60000)) return;
  try {
    const res = await fetch(base.replace('/split/', '/calendar/') + '?days=8');
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Fehler ${res.status}`);
    cal = { at: Date.now(), events: data.events || [] };
  } catch (e) {
    cal = { ...cal, error: e instanceof TypeError ? 'Keine Verbindung – zeige zuletzt geladene Termine.' : e.message };
  }
  try { localStorage.setItem(CAL_KEY, JSON.stringify(cal)); } catch (e) { /* ignorieren */ }
  if (view === 'now' || view === 'week') render();
}
const hhmm = (iso) => new Date(iso).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
const eventItem = (ev) => `<div class="item ev" style="--chip:var(--adhs)"><span class="t"><b><span class="time">${ev.ganztaegig ? 'ganztägig' : esc(hhmm(ev.startIso))}</span>${esc(ev.titel || '(ohne Titel)')}</b><span class="m">${facts([ev.ort, ev.kalender])}</span></span><span class="tag" style="--chip:var(--adhs)">${svg('week')}Termin</span></div>`;

/* ---------- Zustand der Ansicht ---------- */

let view = 'now';
let skip = [];
let lastArea = 'uni';

/* ---------- Aufgaben-Aktionen ---------- */

function addTask(title, areaId, dueKey) {
  const t = title.trim();
  if (!t) return null;
  const due = dueKey === 'today' ? today() : dueKey === 'tomorrow' ? Logic.addDays(today(), 1) : dueKey === 'week' ? Logic.addDays(today(), 7) : undefined;
  const task = { id: uid(), area: areaId, title: t.slice(0, 120), status: 'todo', steps: [], createdAt: Date.now(), updatedAt: Date.now() };
  if (due) task.due = due;
  state.tasks.push(task);
  save();
  return task;
}

function completeTask(t) {
  if (t.repeat && t.due) {
    t.due = Logic.nextDue(t.due, t.repeat);
    t.steps.forEach((s) => { s.done = false; });
    t.status = 'todo';
  } else {
    t.status = 'done';
    t.doneAt = today();
    t.steps.forEach((s) => { s.done = true; });
  }
  touch(t);
  toast(pick(PRAISE));
}

function doneStep(t) {
  const s = t.steps.find((x) => !x.done);
  if (s) {
    s.done = true;
    if (t.status === 'todo') t.status = 'doing';
    touch(t);
    if (t.steps.every((x) => x.done)) completeTask(t);
    else toast(pick(PRAISE));
  } else {
    completeTask(t);
  }
}

/* ---------- Bausteine ---------- */

function quickAdd(fixedArea) {
  const sel = fixedArea ? `<input type="hidden" name="area" value="${fixedArea}">`
    : `<select name="area" aria-label="Bereich">${areas().map((a) => `<option value="${a.id}"${a.id === lastArea ? ' selected' : ''}>${esc(a.name)}</option>`).join('')}</select>`;
  return `<form class="quick" data-quick autocomplete="off">
    <input type="text" name="title" maxlength="120" placeholder="Was geht dir im Kopf rum?" enterkeyhint="done" aria-label="Neue Aufgabe">
    ${sel}
    <select name="due" aria-label="Frist"><option value="">Ohne Frist</option><option value="today">Heute</option><option value="tomorrow">Morgen</option><option value="week">In 1 Woche</option></select>
    <button class="btn primary" type="submit">${svg('plus')}Aufschreiben</button>
  </form>`;
}

function taskItem(t, opts = {}) {
  const td = today();
  const late = t.due && t.due < td && t.status !== 'done';
  const steps = t.steps || [];
  const doneN = steps.filter((s) => s.done).length;
  const meta = facts([t.due ? Logic.dueLabel(t.due, td) : '', steps.length ? `Schritt ${Math.min(doneN + 1, steps.length)} von ${steps.length}` : '', t.repeat ? (t.repeat === 'weekly' ? 'jede Woche' : 'jeden Monat') : '']);
  return `<button class="item${late ? ' late' : ''}${t.status === 'done' ? ' done' : ''}" ${chip(t.area)} data-open="${t.id}">
    <span class="t"><b>${esc(t.title)}</b><span class="m">${meta}</span></span>
    ${opts.tag ? `<span class="tag" ${chip(t.area)}>${svg(t.area)}${esc(area(t.area).name)}</span>` : ''}
  </button>`;
}

/* ---------- Ansichten ---------- */

function greet() {
  const h = new Date().getHours();
  return h < 11 ? 'Guten Morgen' : h < 18 ? 'Hallo' : 'Guten Abend';
}

function renderNow() {
  const td = today();
  const open = state.tasks.filter((t) => t.status !== 'done');
  const week = Logic.weekDays(td);
  const overdue = open.filter((t) => t.due && t.due < td).length;
  const dueWeek = open.filter((t) => t.due && t.due >= td && t.due <= week[6]).length;
  const doneToday = state.tasks.filter((t) => t.doneAt === td).length;

  const chips = `<div class="chips">
    ${overdue ? `<button class="chip warn" data-view="week"><b>${overdue}</b><span>überfällig</span></button>` : ''}
    <button class="chip" ${chip('adhs')} data-view="week"><b>${dueWeek}</b><span>Fristen diese Woche</span></button>
    <button class="chip" ${chip('arbeit')}><b>${doneToday}</b><span>heute erledigt</span></button>
  </div>`;

  return `<div class="inner"><header class="top"><h1>${greet()}, Charlotte</h1><p class="lead">${new Date().toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' })}</p>${(() => {
      const ev = Logic.nextEvent(cal.events, Date.now());
      if (!ev) return '';
      const min = Math.round((Date.parse(ev.startIso) - Date.now()) / 60000);
      const when = min < 60 ? `in ${min} Min.` : `in ${Math.round(min / 60)} Std.`;
      return `<p class="next-event">${svg('week')}<span>Nächster Termin</span><b>${esc(hhmm(ev.startIso))} ${esc(ev.titel || '')}</b><span>${when}</span></p>`;
    })()}</header>
    ${quickAdd()}
    <div class="now-grid">${renderDeck()}
      <div class="now-side">${chips}
        <h3>Deine Bereiche</h3>
        <div class="chips">${areas().map((a) => `<button class="chip" ${chip(a.id)} data-view="${a.id}"><b>${open.filter((t) => t.area === a.id).length}</b><span>${svg(a.id)}${esc(a.name)}</span></button>`).join('')}</div>
      </div>
    </div></div>`;
}

/* ---------- Kartendeck (Jetzt) ---------- */

const RM = matchMedia('(prefers-reduced-motion: reduce)');
const FAN = [[0, 0, 0, 1], [-14, 14, -4, 0.97], [16, 24, 3.5, 0.94], [-8, 34, -6.5, 0.91]];
const FAN_RM = [[0, 0, 0, 1], [0, 12, 0, 0.96], [0, 22, 0, 0.92], [0, 30, 0, 0.88]];
const pose = (i) => { const [x, y, r, sc] = (RM.matches ? FAN_RM : FAN)[Math.min(i, 3)]; return `translate3d(${x}px,${y}px,0) rotate(${r}deg) scale(${sc})`; };
let busy = false;
let drag = null;

function deckCard(t, i) {
  const steps = t.steps || [];
  const k = steps.findIndex((s) => !s.done);
  const step = steps[k];
  return `<article class="dcard${i === 0 ? ' top' : ''}" data-card="${t.id}" style="--chip:var(--${area(t.area).id});z-index:${10 - i};transform:${pose(i)}"${i ? ' aria-hidden="true"' : ''}>
    <div class="dtop"><span class="achip">${svg(t.area)}${esc(area(t.area).name)}</span>${step && step.min ? `<span class="num"><b>${step.min}</b>Min</span>` : ''}</div>
    <div class="dbody">${step ? `<p class="from">aus ${esc(t.title)}</p><h2 class="step">${esc(step.text)}</h2>` : `<h2 class="step">${esc(t.title)}</h2><p class="from">Noch kein Schritt, zerlegen?</p>`}</div>
    <div class="dfoot">${facts([step ? `Schritt ${k + 1} von ${steps.length}` : '', t.due ? Logic.dueLabel(t.due, today()) : ''])}</div>
    <span class="stamp done">Fertig</span><span class="stamp later">Später</span>
  </article>`;
}

function renderDeck() {
  if (!state.tasks.length) return `<div class="deck-wrap"><div class="card deck-empty"><b>Noch nichts hier, das ist okay.</b><p>Schreib oben auf, was dir gerade im Kopf rumgeht. Ein Wort reicht. Sortieren und Zerlegen machen wir danach.</p></div></div>`;
  const cards = Logic.rank(state.tasks, today(), skip).slice(0, 4);
  if (!cards.length) return `<div class="deck-wrap"><div class="card deck-empty"><b>Alles erledigt.</b><p>Genieß die Pause oder schreib oben etwas Neues auf.</p></div></div>`;
  const id = cards[0].id;
  return `<div class="deck-wrap"><div class="deck" id="deck">${cards.map(deckCard).join('')}</div>
    <div class="actions">
      <button class="btn primary" data-act="done" data-id="${id}">${svg('check')}Fertig</button>
      <button class="btn" data-act="later" data-id="${id}">${svg('later')}Später</button>
      <button class="btn" data-act="split" data-id="${id}">${svg('split')}Zerlegen</button>
      <a class="btn" href="../index.html">${svg('clock')}Fokus</a>
    </div>
    <p class="hint swipe-hint"><span>Nach links: Später</span><span>Nach rechts: Fertig</span></p></div>`;
}

// Cards start where they were (prev ids) or collapsed (prev = null), then fan out with a 40ms stagger.
function settleDeck(prev, flown, base = 0) {
  const els = [...document.querySelectorAll('#deck .dcard')];
  const from = els.map((el, i) => {
    if (!prev) return 0;
    const j = prev.indexOf(el.dataset.card);
    return j < 0 || el.dataset.card === flown ? i + 1 : j;
  });
  els.forEach((el, i) => { el.style.transition = 'none'; el.style.transform = pose(from[i]); el.style.opacity = from[i] > 3 ? 0 : 1; });
  void document.body.offsetWidth;
  els.forEach((el, i) => { el.style.transition = ''; el.style.transitionDelay = `${base + i * 40}ms`; el.style.transform = pose(i); el.style.opacity = 1; });
}

function stamps(el, dx) {
  const v = Math.min(Math.abs(dx) / 110, 1);
  el.querySelector('.stamp.done').style.opacity = dx > 0 ? v : 0;
  el.querySelector('.stamp.later').style.opacity = dx < 0 ? v : 0;
}

// dir 1 = Fertig (rechts), -1 = Später (links)
function swipe(dir, dx = 0, dy = 0) {
  const el = document.querySelector('#deck .dcard.top');
  const t = el && find(el.dataset.card);
  if (busy || !t) return;
  busy = true;
  const prev = [...document.querySelectorAll('#deck .dcard')].map((c) => c.dataset.card);
  // Lift the card out of <main> so the re-render below does not cut its flight short.
  const r = $('#deck').getBoundingClientRect();
  Object.assign(el.style, { position: 'fixed', inset: 'auto', left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px`, zIndex: 50, transitionDelay: '0ms' });
  el.classList.remove('dragging', 'top');
  document.body.appendChild(el);
  void el.offsetWidth;
  stamps(el, dir);
  if (RM.matches) { el.style.transition = 'opacity 250ms ease'; }
  else {
    el.style.transition = 'transform 480ms cubic-bezier(.2,.75,.25,1), opacity 480ms ease';
    const rot = dir > 0 ? Math.max(26, dx * 0.065 + 18) : Math.min(-26, dx * 0.065 - 18);
    el.style.transform = `translate3d(${dir * (innerWidth * 0.9 + 160)}px,${dy + (dir > 0 ? 60 : -10)}px,0) rotate(${rot}deg)`;
  }
  el.style.opacity = 0;
  if (dir > 0) doneStep(t); else skip.push(t.id);
  render();
  settleDeck(prev, t.id, RM.matches ? 0 : 110);
  setTimeout(() => { busy = false; }, 260);
  setTimeout(() => el.remove(), 500);
}

document.addEventListener('pointerdown', (e) => {
  const el = e.target.closest('#deck .dcard.top');
  if (!el || busy || drag || e.button > 0) return;
  drag = { el, id: e.pointerId, sx: e.clientX, sy: e.clientY, dx: 0, dy: 0, s: [{ x: 0, t: e.timeStamp }] };
  el.setPointerCapture(e.pointerId);
  el.classList.add('dragging');
  el.style.transitionDelay = '0ms';
});
document.addEventListener('pointermove', (e) => {
  if (!drag || e.pointerId !== drag.id) return; // ignore extra touch points
  const raw = e.clientX - drag.sx;
  // rubber band beyond 170px so the card resists instead of tracking 1:1
  drag.dx = Math.abs(raw) > 170 ? Math.sign(raw) * (170 + (Math.abs(raw) - 170) * 0.35) : raw;
  drag.dy = (e.clientY - drag.sy) * 0.22;
  drag.s.push({ x: raw, t: e.timeStamp });
  if (drag.s.length > 8) drag.s.shift();
  drag.el.style.transform = `translate3d(${drag.dx}px,${drag.dy}px,0) rotate(${RM.matches ? 0 : drag.dx * 0.065}deg)`;
  stamps(drag.el, drag.dx);
});
function dragEnd(e) {
  if (!drag || e.pointerId !== drag.id) return;
  const d = drag;
  drag = null;
  d.el.classList.remove('dragging');
  const last = d.s[d.s.length - 1];
  const first = d.s.find((p) => last.t - p.t <= 90) || d.s[0];
  const v = last.t > first.t ? (last.x - first.x) / (last.t - first.t) : 0;
  const dir = d.dx > 0 ? 1 : -1;
  const fling = Math.abs(v) > 0.11 && Math.sign(v) === dir && Math.abs(d.dx) > 24;
  if (e.type !== 'pointercancel' && (Math.abs(d.dx) > 110 || fling)) swipe(dir, d.dx, d.dy);
  else { d.el.style.transform = pose(0); stamps(d.el, 0); }
}
document.addEventListener('pointerup', dragEnd);
document.addEventListener('pointercancel', dragEnd);

function renderArea(id) {
  const a = area(id);
  const mine = state.tasks.filter((t) => t.area === id);
  const rankIds = Logic.rank(mine, today()).map((t) => t.id);
  const sortOpen = (list) => list.slice().sort((x, y) => rankIds.indexOf(x.id) - rankIds.indexOf(y.id));
  const doing = sortOpen(mine.filter((t) => t.status === 'doing'));
  const todo = sortOpen(mine.filter((t) => t.status === 'todo'));
  const done = mine.filter((t) => t.status === 'done').sort((x, y) => (y.updatedAt || 0) - (x.updatedAt || 0));
  const sec = (title, list, limit) => list.length ? `<h3>${title} (${list.length})</h3><div class="list">${list.slice(0, limit).map((t) => taskItem(t)).join('')}</div>${list.length > limit ? `<p class="hint">… und ${list.length - limit} weitere</p>` : ''}` : '';
  return `<div class="inner"><header class="top"><h1>${esc(a.name)}</h1><p class="lead">${doing.length + todo.length} offen</p></header>
    ${quickAdd(id)}
    ${!mine.length ? '<div class="empty">Hier ist noch nichts. Schreib oben die erste Aufgabe auf.</div>' : ''}
    ${sec('Dran', doing, 5)}${sec('Offen', todo, 8)}${sec('Fertig', done, 5)}</div>`;
}

function renderWeek() {
  const td = today();
  const days = Logic.weekDays(td);
  const open = state.tasks.filter((t) => t.status !== 'done');
  const late = open.filter((t) => t.due && t.due < td);
  const undated = open.filter((t) => !t.due).length;
  return `<div class="inner"><header class="top"><h1>Diese Woche</h1><p class="lead">Fristen und Termine auf einen Blick</p></header>
    ${late.length ? `<div class="card" style="margin-bottom:12px"><h2>Überfällig</h2><div class="list">${late.map((t) => taskItem(t, { tag: true })).join('')}</div></div>` : ''}
    <div class="week">${days.map((d, i) => {
      const items = open.filter((t) => t.due === d);
      const evs = Logic.eventsOn(cal.events, d);
      return `<section class="day${d === td ? ' today' : ''}"><header><b>${DAYNAMES[i]} ${d.slice(8)}.${d.slice(5, 7)}.</b>${WORK_DAYS.includes(i) ? '<span class="work">Drees & Sommer</span>' : ''}</header>
        ${items.length || evs.length ? `<div class="list">${evs.map(eventItem).join('')}${items.map((t) => taskItem(t, { tag: true })).join('')}</div>` : '<span class="muted">–</span>'}</section>`;
    }).join('')}</div>
    <p class="hint">${undated} offene Aufgaben ohne Frist – die findest du in den Bereichen.</p>
    <p class="hint">${getCfg().splitUrl ? `Apple-Kalender${cal.at ? `, Stand ${esc(hhmm(new Date(cal.at).toISOString()))} Uhr` : ''}${cal.error ? `<br>${esc(cal.error)}` : ''} <button class="btn small" data-act="cal-sync">Neu laden</button>` : 'Termine anzeigen: unter Setup den Connector verbinden.'}</p></div>`;
}

function renderSettings() {
  return `<div class="inner"><header class="top"><h1>Einstellungen</h1><p class="lead">Deine Daten bleiben nur auf diesem Gerät.</p></header>
    <div class="card"><h2>Backup</h2>
      <p class="muted">Speichere eine Datei (z. B. in iCloud Drive), um Daten zwischen iPad, iPhone und Mac zu tauschen. Beim Laden wird <b>zusammengeführt</b>, nichts überschrieben.</p>
      <div class="row"><button class="btn primary" data-act="export">Datei speichern</button>
      <label class="btn" style="cursor:pointer">Datei laden<input type="file" accept="application/json,.json" data-import hidden></label></div></div>
    <div class="card" style="margin-top:14px"><h2>Claude zerlegt für dich</h2>
      <p class="muted">Füge hier deinen <b>Connector-Link</b> ein (der mit <b>/mcp/…</b> oder <b>/setup/…</b>). Beim Zerlegen wird nur der <b>Titel</b> der Aufgabe (und deine Notiz) an Claude gesendet.</p>
      <form class="quick" data-cfg autocomplete="off"><input type="text" name="url" placeholder="https://adhs-assistant.….workers.dev/setup/…" value="${esc(getCfg().splitUrl ? '(gespeichert)' : '')}" aria-label="Connector-Link"><button class="btn primary" type="submit">Speichern</button></form>
      ${getCfg().splitUrl ? `<p class="hint">Verbunden</p><div class="row"><a class="btn primary" href="${esc(getCfg().splitUrl.replace('/split/', '/setup/'))}" target="_blank" rel="noopener">Einrichtungsseite öffnen</a><button class="btn small" data-act="cfg-clear">Trennen</button></div>` : ''}</div>
    <div class="card" style="margin-top:14px"><h2>Bereiche benennen</h2>
      <p class="muted">Leer lassen = Standardname.</p>
      <form class="quick" data-names autocomplete="off">${areas().map((a, i) => `<input type="text" name="${a.id}" maxlength="30" value="${esc(a.name)}" placeholder="${AREAS[i].name}" aria-label="Name für ${AREAS[i].name}">`).join('')}<button class="btn primary" type="submit">Speichern</button></form></div>
    <p class="hint">Bitte keine sensiblen Daten (Gesundheit, Passwörter) eintragen.</p></div>`;
}

function render() {
  $('#main').classList.remove('enter');
  $('#main').innerHTML = view === 'now' ? renderNow() : view === 'week' ? renderWeek() : view === 'settings' ? renderSettings() : renderArea(view);
  renderNav();
}

const ICONS = {
  now: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  week: '<rect x="3" y="4" width="18" height="17" rx="3"/><path d="M8 2v4M16 2v4M3 10h18"/>',
  uni: '<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 2.5 9 2.5 12 0v-5"/>',
  arbeit: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>',
  privat: '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
  partei: '<path d="M3 21h18M4 10h16M12 3l9 5H3l9-5Z"/><path d="M6 10v8M10 10v8M14 10v8M18 10v8"/>',
  adhs: '<circle cx="12" cy="12" r="2.5"/><path d="M12 9.5C10 6 10 3.5 12 3c2 .5 2 3 0 6.5ZM12 14.5c2 3.5 2 6 0 6.5-2-.5-2-3 0-6.5ZM9.5 12C6 14 3.5 14 3 12c.5-2 3-2 6.5 0ZM14.5 12c3.5-2 6-2 6.5 0-.5 2-3 2-6.5 0Z"/>',
  settings: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
};
Object.assign(ICONS, {
  check: '<path d="M5 12.5 10 17l9-10"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  clock: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/>',
  split: '<path d="M4 19h16"/><path d="M6 19l5-9 3 5 2-3 2 7"/>',
  later: '<path d="M9 7 4.5 11.5 9 16"/><path d="M4.5 11.5H14a5.5 5.5 0 0 1 0 11"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  z: '<path d="M7 7h10L7 17h10"/>',
  spark: '<path d="M12 3c.6 4.2 2.8 6.4 7 7-4.2.6-6.4 2.8-7 7-.6-4.2-2.8-6.4-7-7 4.2-.6 6.4-2.8 7-7Z"/>',
});
const svg = (id) => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[id] || ICONS.now}</svg>`;

function renderNav() {
  const item = (id, icon, long, short, color) => `<button type="button" data-view="${id}" ${color ? chip(color) : ''}${view === id ? ' aria-current="page"' : ''}>${svg(id)}<span class="long">${long}</span><span class="short">${short}</span></button>`;
  $('#nav').innerHTML = `<p class="brand"><i>${svg('z')}</i>Zentrale</p>
    ${item('now', '', 'Jetzt', 'Jetzt')}${item('week', '', 'Woche', 'Woche')}<div class="sep"></div>
    ${areas().map((a) => item(a.id, '', esc(a.name), a.name === 'ADHS-Projekt' ? 'Projekt' : esc(a.name), a.id)).join('')}<div class="sep"></div>
    ${item('settings', '', 'Einstellungen', 'Setup')}`;
}

const navOrder = () => ['now', 'week', ...AREAS.map((a) => a.id), 'settings'];
function go(v) {
  const changed = v !== view;
  const dir = navOrder().indexOf(v) >= navOrder().indexOf(view) ? 1 : -1;
  view = v; skip = []; render(); window.scrollTo(0, 0);
  if (changed) {
    $('#main').classList.add('enter'); // entrance on view change only
    const h = $('#main h1');
    if (h) {
      h.animate(RM.matches ? [{ opacity: 0 }, { opacity: 1 }]
        : [{ opacity: 0, transform: `translateX(${dir * 48}px)`, filter: 'blur(6px)' }, { opacity: 1, transform: 'none', filter: 'blur(0)' }],
      { duration: 260, easing: 'cubic-bezier(0.23,1,0.32,1)' });
    }
    if (v === 'now') settleDeck(null);
  }
  if (v === 'now' || v === 'week') syncCalendar();
}

/* ---------- Sheet + Toast ---------- */

let toastTimer;
function toast(msg) {
  const el = $('#toast');
  el.textContent = msg; el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2200);
}
function openSheet(html) {
  $('#sheet-card').innerHTML = html;
  $('#sheet').hidden = false;
  document.body.classList.add('locked');
}
function closeSheet() {
  $('#sheet').hidden = true;
  document.body.classList.remove('locked');
  render();
}

function editSheet(id) {
  const t = find(id);
  if (!t) return closeSheet();
  const opt = (v, label, cur) => `<option value="${v}"${v === (cur || '') ? ' selected' : ''}>${label}</option>`;
  openSheet(`<h2>Aufgabe</h2>
    <label>Titel</label><input data-f="title" value="${esc(t.title)}" maxlength="120">
    <label>Bereich</label><select data-f="area">${areas().map((a) => opt(a.id, esc(a.name), t.area)).join('')}</select>
    <label>Frist</label><input type="date" data-f="due" value="${t.due || ''}">
    <label>Wiederholen</label><select data-f="repeat">${opt('', 'Nie', t.repeat)}${opt('weekly', 'Jede Woche', t.repeat)}${opt('monthly', 'Jeden Monat', t.repeat)}</select>
    <label>Status</label><select data-f="status">${opt('todo', 'Offen', t.status)}${opt('doing', 'Dran', t.status)}${opt('done', 'Fertig', t.status)}</select>
    <h3>Schritte</h3>
    ${t.steps.map((s) => `<div class="stepline${s.done ? ' done' : ''}"><input type="checkbox" data-step="${s.id}"${s.done ? ' checked' : ''} aria-label="erledigt"><span>${esc(s.text)}</span>${s.min ? `<em>${s.min} Min</em>` : ''}<button class="btn small" data-rmstep="${s.id}" aria-label="Schritt löschen">${svg('x')}</button></div>`).join('') || '<p class="muted">Noch keine Schritte.</p>'}
    <div class="row" style="margin-top:16px"><button class="btn" data-act="split" data-id="${t.id}">${svg('split')}Zerlegen</button><button class="btn primary" data-act="close">Fertig</button><button class="btn danger" data-act="delete" data-id="${t.id}">Löschen</button></div>`);
  $('#sheet-card').dataset.id = id;
}

function splitSheet(id, focus = true) {
  const t = find(id);
  if (!t) return closeSheet();
  const n = t.steps.length;
  openSheet(`<h2>${esc(t.title)}</h2>
    ${t.steps.map((s) => `<div class="stepline"><span>${esc(s.text)}</span>${s.min ? `<em>${s.min} Min</em>` : ''}</div>`).join('')}
    <form data-split="${t.id}" autocomplete="off">
      <label>${n ? 'Und was kommt danach?' : 'Was ist der allererste Handgriff? (unter 20 Minuten)'}</label>
      <input name="text" maxlength="120" placeholder="${n ? 'Nächster kleiner Schritt' : 'z. B. Datei öffnen und Titel tippen'}" ${focus ? 'autofocus' : ''}>
      <div class="mins" role="radiogroup" aria-label="Dauer">${[5, 10, 20].map((m, i) => `<label class="btn small"><input type="radio" name="min" value="${m}"${i === 1 ? ' checked' : ''} style="width:auto"> ${m} Min.</label>`).join('')}</div>
      <div class="row"><button class="btn primary" type="submit">${svg('plus')}Schritt</button><button class="btn" type="button" data-act="close">Fertig</button></div>
    </form>
    <div id="ai-box">${getCfg().splitUrl
      ? `<button class="btn" type="button" data-act="ai" data-id="${t.id}" style="margin-top:14px">${svg('spark')}Claude schlägt Schritte vor</button>`
      : '<p class="hint">Automatische Vorschläge: in den Einstellungen verbinden.</p>'}</div>
    <p class="hint">Kleine Schritte zuerst – du musst nicht alle kennen. Du kannst später ergänzen.</p>`);
  const input = $('#sheet-card input[name=text]');
  if (input) input.focus();
}

/* ---------- Claude-Vorschläge ---------- */

let aiProposal = [];
async function aiSuggest(t) {
  const box = $('#ai-box');
  box.innerHTML = '<p class="hint">Claude überlegt …</p>';
  try {
    const res = await fetch(getCfg().splitUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: t.title }) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Fehler ${res.status}`);
    aiProposal = data.steps;
    box.innerHTML = `<h3>Vorschlag</h3>${aiProposal.map((s) => `<div class="stepline"><span>${esc(s.text)}</span><em>${s.min} Min</em></div>`).join('')}
      <div class="row" style="margin-top:12px"><button class="btn primary" type="button" data-act="ai-take" data-id="${t.id}">Übernehmen</button><button class="btn" type="button" data-act="ai" data-id="${t.id}">Nochmal</button></div>`;
  } catch (err) {
    const offline = err instanceof TypeError;
    box.innerHTML = `<p class="hint" style="color:var(--warm)">${esc(offline ? 'Keine Verbindung zum Server. Du kannst die Schritte auch selbst eintippen.' : err.message)}</p>
      <button class="btn small" type="button" data-act="ai" data-id="${t.id}">Nochmal versuchen</button>`;
  }
}
function takeAi(id) {
  const t = find(id);
  if (!t || !aiProposal.length) return;
  aiProposal.forEach((s) => t.steps.push({ id: uid(), text: s.text, min: s.min, done: false }));
  aiProposal = [];
  touch(t);
  splitSheet(id);
  toast('Schritte übernommen');
}

/* ---------- Backup ---------- */

function exportData() {
  const blob = new Blob([JSON.stringify(state, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `zentrale-${today()}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function importFile(file) {
  const r = new FileReader();
  r.onload = () => {
    try {
      state = Logic.mergeData(state, JSON.parse(r.result));
      save(); render(); toast('Daten zusammengeführt');
    } catch (e) { toast('Datei nicht lesbar – nichts wurde geändert'); }
  };
  r.readAsText(file);
}

/* ---------- Ereignisse ---------- */

document.addEventListener('click', (e) => {
  const v = e.target.closest('[data-view]');
  if (v) return go(v.dataset.view);
  const o = e.target.closest('[data-open]');
  if (o) return editSheet(o.dataset.open);
  const rm = e.target.closest('[data-rmstep]');
  if (rm) {
    const t = find($('#sheet-card').dataset.id);
    t.steps = t.steps.filter((s) => s.id !== rm.dataset.rmstep); touch(t); return editSheet(t.id);
  }
  const b = e.target.closest('[data-act]');
  if (!b) return;
  const t = b.dataset.id ? find(b.dataset.id) : null;
  switch (b.dataset.act) {
    case 'done': if (t) swipe(1); break;
    case 'later': if (t) swipe(-1); break;
    case 'split': if (t) splitSheet(t.id); break;
    case 'close': closeSheet(); break;
    case 'delete': if (t && confirm('Diese Aufgabe löschen?')) { state.tasks = state.tasks.filter((x) => x.id !== t.id); save(); closeSheet(); } break;
    case 'export': exportData(); break;
    case 'ai': if (t) aiSuggest(t); break;
    case 'ai-take': takeAi(b.dataset.id); break;
    case 'cal-sync': syncCalendar(true); toast('Lade Termine …'); break;
    case 'cfg-clear': { const { splitUrl, ...rest } = getCfg(); setCfg(rest); } render(); toast('Getrennt'); break;
    default:
  }
});

document.addEventListener('submit', (e) => {
  const f = e.target;
  if (f.matches('[data-quick]')) {
    e.preventDefault();
    const el = f.elements;
    const title = el.title.value;
    if (!title.trim()) return;
    lastArea = el.area.value;
    addTask(title, el.area.value, el.due.value);
    render(); toast('Aufgeschrieben. Aus dem Kopf raus.');
    const inp = $('[data-quick] input[type=text]'); if (inp) inp.focus();
  } else if (f.matches('[data-cfg]')) {
    e.preventDefault();
    const url = Logic.splitEndpoint(f.elements.url.value);
    if (!url) return toast('Link ohne Schlüssel: Er muss /mcp/… oder /setup/… mit dem langen Code danach enthalten.');
    setCfg({ ...getCfg(), splitUrl: url });
    render(); toast('Verbunden'); syncCalendar(true);
  } else if (f.matches('[data-names]')) {
    e.preventDefault();
    const names = {};
    AREAS.forEach((a) => { const v = f.elements[a.id].value.trim().slice(0, 30); if (v && v !== a.name) names[a.id] = v; });
    setCfg({ ...getCfg(), names });
    render(); toast('Namen gespeichert');
  } else if (f.matches('[data-split]')) {
    e.preventDefault();
    const t = find(f.dataset.split);
    const text = f.elements.text.value.trim();
    if (t && text) {
      t.steps.push({ id: uid(), text: text.slice(0, 120), min: Number(f.elements.min.value) || 10, done: false });
      touch(t);
    }
    splitSheet(f.dataset.split);
  }
});

document.addEventListener('change', (e) => {
  const el = e.target;
  if (el.matches('[data-import]')) { if (el.files[0]) importFile(el.files[0]); el.value = ''; return; }
  const id = $('#sheet-card').dataset.id;
  const t = id && !$('#sheet').hidden ? find(id) : null;
  if (!t) return;
  if (el.dataset.f) {
    const f = el.dataset.f;
    if (f === 'title') { if (el.value.trim()) t.title = el.value.trim().slice(0, 120); }
    else if (f === 'due' || f === 'repeat') { if (el.value) t[f] = el.value; else delete t[f]; }
    else { t[f] = el.value; if (f === 'status' && el.value === 'done') t.doneAt = today(); }
    touch(t);
  } else if (el.dataset.step) {
    const s = t.steps.find((x) => x.id === el.dataset.step);
    if (s) { s.done = el.checked; touch(t); editSheet(t.id); }
  }
});

$('#sheet').addEventListener('click', (e) => { if (e.target.id === 'sheet') closeSheet(); });
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !$('#sheet').hidden) return closeSheet();
  if ((e.key === 'ArrowRight' || e.key === 'ArrowLeft') && view === 'now' && $('#sheet').hidden && !e.target.closest('input,select,textarea')) {
    e.preventDefault();
    swipe(e.key === 'ArrowRight' ? 1 : -1);
  }
});

render();
settleDeck(null);
syncCalendar();
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
