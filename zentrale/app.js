'use strict';
/* Zentrale – UI. Reine Logik steht in logic.js (Global `Logic`). Daten nur lokal. */

const STORE_KEY = 'zentrale-v1';
const AREAS = [
  { id: 'uni', name: 'Uni', icon: '🎓' },
  { id: 'arbeit', name: 'Arbeit', icon: '💼' },
  { id: 'privat', name: 'Privat', icon: '🏠' },
  { id: 'partei', name: 'Partei', icon: '🏛️' },
  { id: 'adhs', name: 'ADHS-Projekt', icon: '🧩' },
];
const WORK_DAYS = [0, 3]; // Montag, Donnerstag (Drees & Sommer)
const PRAISE = ['Stark! 🎉', 'Geschafft ✨', 'Ein Ding weniger 🌱', 'Gut gemacht 💜', 'Das zählt 🙌'];
const DAYNAMES = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
const today = () => new Date().toLocaleDateString('sv');
const pick = (a) => a[Math.floor(Math.random() * a.length)];
// Eigene Namen aus den Einstellungen; IDs und Farben bleiben fest
const areas = () => { const n = getCfg().names || {}; return AREAS.map((a) => ({ ...a, name: n[a.id] || a.name })); };
const area = (id) => areas().find((a) => a.id === id) || areas()[0];
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
const eventItem = (ev) => `<div class="item ev" style="--chip:var(--line)"><span class="t"><b>${ev.ganztaegig ? 'ganztägig' : esc(hhmm(ev.startIso))} · ${esc(ev.titel || '(ohne Titel)')}</b><span class="m">${esc([ev.ort, ev.kalender].filter(Boolean).join(' · '))}</span></span><span class="tag" style="--chip:var(--line)">📅</span></div>`;

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
    : `<select name="area" aria-label="Bereich">${areas().map((a) => `<option value="${a.id}"${a.id === lastArea ? ' selected' : ''}>${a.icon} ${esc(a.name)}</option>`).join('')}</select>`;
  return `<form class="quick" data-quick autocomplete="off">
    <input type="text" name="title" maxlength="120" placeholder="Was geht dir im Kopf rum?" enterkeyhint="done" aria-label="Neue Aufgabe">
    ${sel}
    <select name="due" aria-label="Frist"><option value="">Ohne Frist</option><option value="today">Heute</option><option value="tomorrow">Morgen</option><option value="week">In 1 Woche</option></select>
    <button class="btn primary" type="submit">＋ Aufschreiben</button>
  </form>`;
}

function taskItem(t, opts = {}) {
  const td = today();
  const late = t.due && t.due < td && t.status !== 'done';
  const steps = t.steps || [];
  const doneN = steps.filter((s) => s.done).length;
  const progress = steps.length ? `<div class="bar" aria-hidden="true"><i style="width:${Math.round((doneN / steps.length) * 100)}%"></i></div>` : '';
  const meta = [t.due ? Logic.dueLabel(t.due, td) : '', steps.length ? `${doneN}/${steps.length} Schritte` : '', t.repeat ? '🔁' : ''].filter(Boolean).join(' · ');
  return `<button class="item${late ? ' late' : ''}${t.status === 'done' ? ' done' : ''}" ${chip(t.area)} data-open="${t.id}">
    <span class="t"><b>${esc(t.title)}</b><span class="m">${esc(meta)}</span>${progress}</span>
    ${opts.tag ? `<span class="tag" ${chip(t.area)}>${area(t.area).icon} ${esc(area(t.area).name)}</span>` : ''}
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
  const next = Logic.pickNext(state.tasks, td, skip);
  const week = Logic.weekDays(td);
  const overdue = open.filter((t) => t.due && t.due < td).length;
  const dueWeek = open.filter((t) => t.due && t.due >= td && t.due <= week[6]).length;
  const doneToday = state.tasks.filter((t) => t.doneAt === td).length;

  let hero;
  if (!state.tasks.length) {
    hero = `<div class="card empty"><b>Noch nichts hier – das ist okay.</b><br>Schreib oben auf, was dir gerade im Kopf rumgeht. Ein Wort reicht. Sortieren und Zerlegen machen wir danach.</div>`;
  } else if (!next) {
    hero = `<div class="card hero" ${chip('adhs')}><p class="kicker">Alles erledigt</p><h2>Nichts offen. 🎉</h2><p class="why">Genieß die Pause oder schreib oben etwas Neues auf.</p></div>`;
  } else {
    const t = next.task;
    const stepText = next.step ? next.step.text : null;
    hero = `<div class="card hero" ${chip(t.area)}>
      <p class="kicker">${area(t.area).icon} ${esc(area(t.area).name)} · Dein nächster Schritt</p>
      <h2>${esc(stepText || t.title)}</h2>
      <p class="why">${stepText ? `Aus: ${esc(t.title)}${next.step.min ? ` · ca. ${next.step.min} Min.` : ''}<br>` : 'Noch kein Schritt festgelegt – zerlege die Aufgabe, dann wird sie klein.<br>'}${esc(next.reason)}</p>
      <div class="row">
        <button class="btn primary" data-act="done" data-id="${t.id}">✅ Fertig</button>
        <button class="btn" data-act="later" data-id="${t.id}">⏭ Später</button>
        <button class="btn" data-act="split" data-id="${t.id}">⛰️ ${t.steps.length ? 'Schritte ändern' : 'Zu groß? Zerlegen'}</button>
        <a class="btn" href="../index.html">⏱️ Fokus starten</a>
      </div>
    </div>`;
  }

  const after = Logic.rank(state.tasks, td, skip).filter((t) => !next || t.id !== next.task.id).slice(0, 3);
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
      return `<p class="lead">📅 Nächster Termin: <b>${esc(hhmm(ev.startIso))} ${esc(ev.titel || '')}</b> (${when})</p>`;
    })()}</header>
    ${quickAdd()}${hero}${chips}
    ${after.length ? `<h3>Danach</h3><div class="list">${after.map((t) => taskItem(t, { tag: true })).join('')}</div>` : ''}
    <h3>Deine Bereiche</h3>
    <div class="chips">${areas().map((a) => `<button class="chip" ${chip(a.id)} data-view="${a.id}"><b>${open.filter((t) => t.area === a.id).length}</b><span>${a.icon} ${esc(a.name)}</span></button>`).join('')}</div></div>`;
}

function renderArea(id) {
  const a = area(id);
  const mine = state.tasks.filter((t) => t.area === id);
  const rankIds = Logic.rank(mine, today()).map((t) => t.id);
  const sortOpen = (list) => list.slice().sort((x, y) => rankIds.indexOf(x.id) - rankIds.indexOf(y.id));
  const doing = sortOpen(mine.filter((t) => t.status === 'doing'));
  const todo = sortOpen(mine.filter((t) => t.status === 'todo'));
  const done = mine.filter((t) => t.status === 'done').sort((x, y) => (y.updatedAt || 0) - (x.updatedAt || 0));
  const sec = (title, list, limit) => list.length ? `<h3>${title} (${list.length})</h3><div class="list">${list.slice(0, limit).map((t) => taskItem(t)).join('')}</div>${list.length > limit ? `<p class="hint">… und ${list.length - limit} weitere</p>` : ''}` : '';
  return `<div class="inner"><header class="top"><h1>${a.icon} ${esc(a.name)}</h1><p class="lead">${doing.length + todo.length} offen</p></header>
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
  return `<div class="inner"><header class="top"><h1>📅 Diese Woche</h1><p class="lead">Fristen und Termine auf einen Blick</p></header>
    ${late.length ? `<div class="card" style="margin-bottom:12px"><h2>⚠️ Überfällig</h2><div class="list">${late.map((t) => taskItem(t, { tag: true })).join('')}</div></div>` : ''}
    <div class="week">${days.map((d, i) => {
      const items = open.filter((t) => t.due === d);
      const evs = Logic.eventsOn(cal.events, d);
      return `<section class="day${d === td ? ' today' : ''}"><header><b>${DAYNAMES[i]} ${d.slice(8)}.${d.slice(5, 7)}.</b>${WORK_DAYS.includes(i) ? '<span class="work">💼 Drees & Sommer</span>' : ''}</header>
        ${items.length || evs.length ? `<div class="list">${evs.map(eventItem).join('')}${items.map((t) => taskItem(t, { tag: true })).join('')}</div>` : '<span class="muted">–</span>'}</section>`;
    }).join('')}</div>
    <p class="hint">${undated} offene Aufgaben ohne Frist – die findest du in den Bereichen.</p>
    <p class="hint">${getCfg().splitUrl ? `📅 Apple-Kalender${cal.at ? ` · Stand ${esc(hhmm(new Date(cal.at).toISOString()))}` : ''}${cal.error ? ` · ⚠️ ${esc(cal.error)}` : ''} <button class="btn small" data-act="cal-sync">Neu laden</button>` : '📅 Termine anzeigen: unter Setup den Connector verbinden.'}</p></div>`;
}

function renderSettings() {
  return `<div class="inner"><header class="top"><h1>⚙️ Einstellungen</h1><p class="lead">Deine Daten bleiben nur auf diesem Gerät.</p></header>
    <div class="card"><h2>💾 Backup</h2>
      <p class="muted">Speichere eine Datei (z. B. in iCloud Drive), um Daten zwischen iPad, iPhone und Mac zu tauschen. Beim Laden wird <b>zusammengeführt</b>, nichts überschrieben.</p>
      <div class="row"><button class="btn primary" data-act="export">Datei speichern</button>
      <label class="btn" style="cursor:pointer">Datei laden<input type="file" accept="application/json,.json" data-import hidden></label></div></div>
    <div class="card" style="margin-top:14px"><h2>✨ Claude zerlegt für dich</h2>
      <p class="muted">Füge hier deinen <b>Connector-Link</b> ein (der mit <b>/mcp/…</b> oder <b>/setup/…</b>). Beim Zerlegen wird nur der <b>Titel</b> der Aufgabe (und deine Notiz) an Claude gesendet.</p>
      <form class="quick" data-cfg autocomplete="off"><input type="text" name="url" placeholder="https://adhs-assistant.….workers.dev/setup/…" value="${esc(getCfg().splitUrl ? '(gespeichert)' : '')}" aria-label="Connector-Link"><button class="btn primary" type="submit">Speichern</button></form>
      ${getCfg().splitUrl ? `<p class="hint">✅ Verbunden.</p><div class="row"><a class="btn primary" href="${esc(getCfg().splitUrl.replace('/split/', '/setup/'))}" target="_blank" rel="noopener">🔑 Einrichtungsseite öffnen (API-Key)</a><button class="btn small" data-act="cfg-clear">Trennen</button></div>` : ''}</div>
    <div class="card" style="margin-top:14px"><h2>🏷️ Bereiche benennen</h2>
      <p class="muted">Leer lassen = Standardname.</p>
      <form class="quick" data-names autocomplete="off">${areas().map((a, i) => `<input type="text" name="${a.id}" maxlength="30" value="${esc(a.name)}" placeholder="${AREAS[i].icon} ${AREAS[i].name}" aria-label="Name für ${AREAS[i].name}">`).join('')}<button class="btn primary" type="submit">Speichern</button></form></div>
    <p class="hint">Bitte keine sensiblen Daten (Gesundheit, Passwörter) eintragen.</p></div>`;
}

function render() {
  $('#main').innerHTML = view === 'now' ? renderNow() : view === 'week' ? renderWeek() : view === 'settings' ? renderSettings() : renderArea(view);
  renderNav();
}

function renderNav() {
  const item = (id, icon, long, short, color) => `<button type="button" data-view="${id}" ${color ? chip(color) : 'style="--chip:var(--line)"'}${view === id ? ' aria-current="page"' : ''}><i>${icon}</i><span class="long">${long}</span><span class="short">${short}</span></button>`;
  $('#nav').innerHTML = `<p class="brand">Zentrale</p>
    ${item('now', '🎯', 'Jetzt', 'Jetzt')}${item('week', '📅', 'Woche', 'Woche')}<div class="sep"></div>
    ${areas().map((a) => item(a.id, a.icon, esc(a.name), a.name === 'ADHS-Projekt' ? 'Projekt' : esc(a.name), a.id)).join('')}<div class="sep"></div>
    ${item('settings', '⚙️', 'Einstellungen', 'Setup')}`;
}

function go(v) { view = v; skip = []; render(); window.scrollTo(0, 0); if (v === 'now' || v === 'week') syncCalendar(); }

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
    <label>Bereich</label><select data-f="area">${areas().map((a) => opt(a.id, `${a.icon} ${esc(a.name)}`, t.area)).join('')}</select>
    <label>Frist</label><input type="date" data-f="due" value="${t.due || ''}">
    <label>Wiederholen</label><select data-f="repeat">${opt('', 'Nie', t.repeat)}${opt('weekly', 'Jede Woche', t.repeat)}${opt('monthly', 'Jeden Monat', t.repeat)}</select>
    <label>Status</label><select data-f="status">${opt('todo', 'Offen', t.status)}${opt('doing', 'Dran', t.status)}${opt('done', 'Fertig', t.status)}</select>
    <h3>Schritte</h3>
    ${t.steps.map((s) => `<div class="stepline${s.done ? ' done' : ''}"><input type="checkbox" data-step="${s.id}"${s.done ? ' checked' : ''} aria-label="erledigt"><span>${esc(s.text)}${s.min ? ` · ${s.min} Min.` : ''}</span><button class="btn small" data-rmstep="${s.id}" aria-label="Schritt löschen">✕</button></div>`).join('') || '<p class="muted">Noch keine Schritte.</p>'}
    <div class="row" style="margin-top:16px"><button class="btn" data-act="split" data-id="${t.id}">⛰️ Zerlegen</button><button class="btn primary" data-act="close">Fertig</button><button class="btn danger" data-act="delete" data-id="${t.id}">Löschen</button></div>`);
  $('#sheet-card').dataset.id = id;
}

function splitSheet(id, focus = true) {
  const t = find(id);
  if (!t) return closeSheet();
  const n = t.steps.length;
  openSheet(`<h2>⛰️ ${esc(t.title)}</h2>
    ${t.steps.map((s) => `<div class="stepline"><span>${n ? '👣' : ''} ${esc(s.text)}${s.min ? ` · ${s.min} Min.` : ''}</span></div>`).join('')}
    <form data-split="${t.id}" autocomplete="off">
      <label>${n ? 'Und was kommt danach?' : 'Was ist der allererste Handgriff? (unter 20 Minuten)'}</label>
      <input name="text" maxlength="120" placeholder="${n ? 'Nächster kleiner Schritt' : 'z. B. Datei öffnen und Titel tippen'}" ${focus ? 'autofocus' : ''}>
      <div class="mins" role="radiogroup" aria-label="Dauer">${[5, 10, 20].map((m, i) => `<label class="btn small"><input type="radio" name="min" value="${m}"${i === 1 ? ' checked' : ''} style="width:auto"> ${m} Min.</label>`).join('')}</div>
      <div class="row"><button class="btn primary" type="submit">＋ Schritt</button><button class="btn" type="button" data-act="close">Fertig</button></div>
    </form>
    <div id="ai-box">${getCfg().splitUrl
      ? `<button class="btn" type="button" data-act="ai" data-id="${t.id}" style="margin-top:14px">✨ Claude schlägt Schritte vor</button>`
      : '<p class="hint">✨ Automatische Vorschläge: in den Einstellungen verbinden.</p>'}</div>
    <p class="hint">Kleine Schritte zuerst – du musst nicht alle kennen. Du kannst später ergänzen.</p>`);
  const input = $('#sheet-card input[name=text]');
  if (input) input.focus();
}

/* ---------- Claude-Vorschläge ---------- */

let aiProposal = [];
async function aiSuggest(t) {
  const box = $('#ai-box');
  box.innerHTML = '<p class="hint">⏳ Claude überlegt …</p>';
  try {
    const res = await fetch(getCfg().splitUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: t.title }) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Fehler ${res.status}`);
    aiProposal = data.steps;
    box.innerHTML = `<h3>Vorschlag</h3>${aiProposal.map((s) => `<div class="stepline"><span>👣 ${esc(s.text)} · ${s.min} Min.</span></div>`).join('')}
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
  toast('Schritte übernommen ✅');
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
      save(); render(); toast('Daten zusammengeführt ✅');
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
    case 'done': if (t) { doneStep(t); render(); } break;
    case 'later': if (t) { skip.push(t.id); render(); } break;
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
    render(); toast('Aufgeschrieben – aus dem Kopf raus ✅');
    const inp = $('[data-quick] input[type=text]'); if (inp) inp.focus();
  } else if (f.matches('[data-cfg]')) {
    e.preventDefault();
    const url = Logic.splitEndpoint(f.elements.url.value);
    if (!url) return toast('Link ohne Schlüssel: Er muss /mcp/… oder /setup/… mit dem langen Code danach enthalten.');
    setCfg({ ...getCfg(), splitUrl: url });
    render(); toast('Verbunden ✅'); syncCalendar(true);
  } else if (f.matches('[data-names]')) {
    e.preventDefault();
    const names = {};
    AREAS.forEach((a) => { const v = f.elements[a.id].value.trim().slice(0, 30); if (v && v !== a.name) names[a.id] = v; });
    setCfg({ ...getCfg(), names });
    render(); toast('Namen gespeichert ✅');
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
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#sheet').hidden) closeSheet(); });

render();
syncCalendar();
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
