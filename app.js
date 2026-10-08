'use strict';

const WORK_MIN = 20;
const PAUSE_MIN = 5;
const STORE_KEY = 'fokus-heute-v1';
const RING = 2 * Math.PI * 54;

const $ = (sel) => document.querySelector(sel);
const views = ['plan', 'step', 'today', 'timer'];

/* ---------- Speicher (nur lokal) ---------- */

const today = () => new Date().toLocaleDateString('sv'); // YYYY-MM-DD

function load() {
  try {
    const s = JSON.parse(localStorage.getItem(STORE_KEY));
    if (s && s.date === today()) return s;
  } catch (e) { /* leer oder blockiert */ }
  return { date: today(), tasks: [], timer: null };
}
function save() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* ignorieren */ }
}

let state = load();

/* ---------- Hilfen ---------- */

function show(name) {
  views.forEach((v) => { $('#view-' + v).hidden = v !== name; });
  window.scrollTo(0, 0);
}
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
const findTask = (id) => state.tasks.find((t) => t.id === id);
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

/* ---------- 1. Morgenplanung ---------- */

$('#plan-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const f = e.target;
  const titles = ['t0', 't1', 't2'].map((n) => f[n].value.trim()).filter(Boolean);
  if (!titles.length) { $('#plan-error').hidden = false; return; }
  $('#plan-error').hidden = true;
  state = {
    date: today(),
    timer: null,
    tasks: titles.map((title, i) => ({ id: Date.now() + i, title, step: '', criteria: [], done: false, steps: 0 })),
  };
  save();
  f.reset();
  nextSetup();
});

// Führt nacheinander durch alle Aufgaben ohne Schritt
function nextSetup() {
  const t = state.tasks.find((x) => !x.done && !x.step);
  if (t) openStep(t.id, 'setup');
  else renderToday();
}

/* ---------- 2. Mikroschritt ---------- */

let stepCtx = null;

function openStep(id, mode) {
  const t = findTask(id);
  stepCtx = { id, mode };
  const f = $('#step-form');
  f.reset();
  const kicker = { setup: `Aufgabe ${state.tasks.indexOf(t) + 1} von ${state.tasks.length}`, next: '👏 Super! Was kommt jetzt?', edit: '✏️ Schritt ändern' };
  $('#step-kicker').textContent = kicker[mode];
  $('#step-task').textContent = t.title;
  if (mode === 'edit') {
    f.step.value = t.step;
    t.criteria.forEach((c, i) => { f['c' + i].value = c; });
  }
  $('#step-cancel').textContent = mode === 'next' ? '🏁 Aufgabe ist fertig' : 'Abbrechen';
  $('#step-cancel').hidden = mode === 'setup';
  show('step');
  setTimeout(() => f.step.focus(), 50);
}

$('#step-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const f = e.target;
  const t = findTask(stepCtx.id);
  t.step = f.step.value.trim();
  t.criteria = ['c0', 'c1', 'c2'].map((n) => f[n].value.trim()).filter(Boolean);
  save();
  if (stepCtx.mode === 'setup') nextSetup();
  else renderToday();
});

$('#step-cancel').addEventListener('click', () => {
  if (stepCtx.mode === 'next') finishTask(stepCtx.id);
  else renderToday();
});

/* ---------- 3. Heute ---------- */

function renderToday() {
  const list = $('#task-list');
  const open = state.tasks.filter((t) => !t.done);
  const done = state.tasks.length - open.length;
  $('#progress').innerHTML = `<b>${done}</b> von <b>${state.tasks.length}</b> geschafft ${'✅'.repeat(done)}`;
  $('#all-done').hidden = open.length > 0;

  list.innerHTML = state.tasks.map((t) => {
    if (t.done) {
      return `<li class="task done"><p class="task-title">✅ ${esc(t.title)}</p></li>`;
    }
    if (!t.step) {
      return `<li class="task"><p class="task-title">${esc(t.title)}</p>
        <button class="btn primary" data-act="edit" data-id="${t.id}">👣 Nächsten Schritt festlegen</button></li>`;
    }
    const crit = t.criteria.length
      ? `<p class="label">🎯 <b>Fertig, wenn:</b></p><ul class="criteria">${t.criteria.map((c) => `<li>${esc(c)}</li>`).join('')}</ul>`
      : '';
    return `<li class="task">
      <p class="task-title">${esc(t.title)}</p>
      <div class="next"><p class="label">👣 Nur das hier:</p><p>${esc(t.step)}</p></div>
      ${crit}
      <div class="row">
        <button class="btn primary" data-act="focus" data-id="${t.id}">▶️ ${WORK_MIN} Min Fokus</button>
        <button class="btn ghost" data-act="stepdone" data-id="${t.id}">✅ Schritt geschafft</button>
      </div>
      <button class="link" data-act="edit" data-id="${t.id}">✏️ Schritt ändern</button>
    </li>`;
  }).join('');
  show('today');
}

$('#task-list').addEventListener('click', (e) => {
  const b = e.target.closest('button[data-act]');
  if (!b) return;
  const id = Number(b.dataset.id);
  const act = b.dataset.act;
  if (act === 'edit') openStep(id, findTask(id).step ? 'edit' : 'setup');
  if (act === 'focus') startTimer(id);
  if (act === 'stepdone') completeStep(id);
});

$('#new-day').addEventListener('click', () => {
  if (!confirm('Neu planen? Die heutige Liste wird gelöscht.')) return;
  state = { date: today(), tasks: [], timer: null };
  save();
  show('plan');
});

/* ---------- 4. Abhaken + Belohnung ---------- */

const STEP_PRAISE = [
  ['🎉', '<b>Schritt geschafft!</b> Genau so geht das.'],
  ['⭐', '<b>Stark!</b> Ein Schritt nach dem anderen.'],
  ['🚀', '<b>Läuft!</b> Dein Gehirn hat gerade gewonnen.'],
  ['🌱', '<b>Fortschritt!</b> Klein ist auch groß.'],
  ['💪', '<b>Erledigt!</b> Du bist dran geblieben.'],
];
const TASK_PRAISE = [
  ['🏆', '<b>Aufgabe komplett fertig!</b> Richtig gut.'],
  ['🥇', '<b>Abgehakt!</b> Das war nicht nichts.'],
  ['🌟', '<b>Geschafft!</b> Gönn dir kurz was Schönes.'],
];

let afterReward = null;

function reward([emoji, text], then) {
  $('#reward-emoji').textContent = emoji;
  $('#reward-text').innerHTML = text;
  $('#reward').hidden = false;
  confetti(emoji);
  chime('reward');
  afterReward = then;
}
$('#reward-ok').addEventListener('click', () => {
  $('#reward').hidden = true;
  const fn = afterReward; afterReward = null;
  if (fn) fn();
});

function confetti(main) {
  const box = $('#confetti');
  const set = [main, '✨', '🎊', '⭐', '💚'];
  for (let i = 0; i < 28; i++) {
    const s = document.createElement('span');
    s.className = 'bit';
    s.textContent = pick(set);
    s.style.left = Math.random() * 100 + 'vw';
    s.style.setProperty('--x', (Math.random() * 120 - 60) + 'px');
    s.style.setProperty('--r', (Math.random() * 720 - 360) + 'deg');
    s.style.setProperty('--d', (1.4 + Math.random() * 1.4) + 's');
    s.style.animationDelay = Math.random() * 0.4 + 's';
    box.appendChild(s);
    setTimeout(() => s.remove(), 3500);
  }
}

function completeStep(id) {
  const t = findTask(id);
  t.steps += 1;
  t.step = '';
  t.criteria = [];
  save();
  reward(pick(STEP_PRAISE), () => openStep(id, 'next'));
}

function finishTask(id) {
  const t = findTask(id);
  t.done = true;
  t.step = '';
  save();
  reward(pick(TASK_PRAISE), renderToday);
}

/* ---------- 5. Fokus-Timer ---------- */

let tick = null;
let wakeLock = null;

function startTimer(id) {
  unlockAudio();
  state.timer = { id, start: Date.now(), workEnd: Date.now() + WORK_MIN * 60000 };
  save();
  keepAwake();
  runTimer();
}

// Phase immer aus Zeitstempeln berechnen: funktioniert auch nach Hintergrund oder Neuladen
function phaseOf(tm, now) {
  const pauseEnd = tm.workEnd + PAUSE_MIN * 60000;
  if (now < tm.workEnd) return { phase: 'work', left: tm.workEnd - now, total: WORK_MIN * 60000 };
  if (now < pauseEnd) return { phase: 'pause', left: pauseEnd - now, total: PAUSE_MIN * 60000 };
  return { phase: 'end', left: 0, total: 1 };
}

let lastPhase = null;

function runTimer() {
  const tm = state.timer;
  const t = findTask(tm.id);
  $('#timer-task').textContent = t ? '👣 ' + t.step : '';
  lastPhase = phaseOf(tm, Date.now()).phase;
  show('timer');
  clearInterval(tick);
  renderTimer();
  tick = setInterval(renderTimer, 250);
}

function renderTimer() {
  const tm = state.timer;
  if (!tm) return;
  const p = phaseOf(tm, Date.now());
  if (p.phase !== lastPhase) {
    chime(p.phase === 'pause' ? 'stop' : 'end');
    lastPhase = p.phase;
  }
  const view = $('#view-timer');
  view.classList.toggle('pause', p.phase !== 'work');
  view.classList.toggle('stopped', p.phase === 'end');

  const sec = Math.ceil(p.left / 1000);
  $('#clock').textContent = `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
  $('#ring-fg').style.strokeDashoffset = String(RING * (1 - p.left / p.total));

  const next = $('#timer-next');
  if (p.phase === 'work') {
    $('#timer-phase').innerHTML = '🧠 <b>Fokus</b>';
    $('#timer-hint').innerHTML = 'Nur <b>dieser eine</b> Schritt. Handy weg. 📵';
    next.hidden = true;
    $('#timer-stop').textContent = '⏹️ Abbrechen';
  } else if (p.phase === 'pause') {
    $('#timer-phase').innerHTML = '☕ <b>Pause</b>';
    $('#timer-hint').innerHTML = '⏰ <b>Stopp!</b> Aufstehen, trinken, strecken.';
    next.hidden = false;
    next.textContent = '✅ Schritt geschafft';
    $('#timer-stop').textContent = '⏹️ Beenden';
  } else {
    clearInterval(tick);
    releaseWake();
    $('#timer-phase').innerHTML = '🔔 <b>Pause vorbei</b>';
    $('#timer-hint').innerHTML = 'Schritt <b>geschafft</b> oder <b>noch eine Runde</b>?';
    next.hidden = false;
    next.textContent = '✅ Schritt geschafft';
    $('#timer-stop').textContent = '🔁 Noch eine Runde';
  }
}

function stopTimer() {
  clearInterval(tick);
  releaseWake();
  state.timer = null;
  save();
}

$('#timer-stop').addEventListener('click', () => {
  const tm = state.timer;
  const ended = tm && phaseOf(tm, Date.now()).phase === 'end';
  stopTimer();
  if (ended && findTask(tm.id)) startTimer(tm.id);
  else renderToday();
});

$('#timer-next').addEventListener('click', () => {
  const id = state.timer.id;
  stopTimer();
  completeStep(id);
});

// Bildschirm wach halten, solange der Timer läuft
async function keepAwake() {
  try { wakeLock = await navigator.wakeLock.request('screen'); } catch (e) { wakeLock = null; }
}
function releaseWake() {
  if (wakeLock) { wakeLock.release().catch(() => {}); wakeLock = null; }
}
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && state.timer) {
    if (phaseOf(state.timer, Date.now()).phase !== 'end') keepAwake();
    renderTimer();
  }
});

/* ---------- Ton (Web Audio, kein Download nötig) ---------- */

let audio = null;

function unlockAudio() {
  try {
    audio = audio || new (window.AudioContext || window.webkitAudioContext)();
    if (audio.state === 'suspended') audio.resume();
    // stiller Ton, damit iOS den Ton später erlaubt
    const o = audio.createOscillator(); const g = audio.createGain();
    g.gain.value = 0; o.connect(g).connect(audio.destination); o.start(); o.stop(audio.currentTime + 0.05);
  } catch (e) { audio = null; }
}

function chime(kind) {
  if (!audio) unlockAudio();
  if (!audio) return;
  const notes = {
    stop: [880, 660, 880, 660, 880],   // harter Stopp: deutlich
    end: [523, 659, 784],              // Pause vorbei: freundlich
    reward: [659, 784, 1047],          // Belohnung: kurz hell
  }[kind];
  const now = audio.currentTime;
  notes.forEach((f, i) => {
    const o = audio.createOscillator();
    const g = audio.createGain();
    o.type = kind === 'stop' ? 'square' : 'sine';
    o.frequency.value = f;
    const t0 = now + i * 0.22;
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(kind === 'stop' ? 0.25 : 0.35, t0 + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.4);
    o.connect(g).connect(audio.destination);
    o.start(t0);
    o.stop(t0 + 0.45);
  });
  if (navigator.vibrate) navigator.vibrate(kind === 'stop' ? [300, 150, 300, 150, 300] : 150);
}

/* ---------- Start ---------- */

function init() {
  if (state.timer && findTask(state.timer.id)) runTimer();
  else if (state.tasks.length) {
    state.timer = null;
    const missing = state.tasks.find((t) => !t.done && !t.step);
    if (missing) nextSetup(); else renderToday();
  } else show('plan');
}
init();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
}
