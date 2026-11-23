'use strict';
/* Reine Logik der Zentrale (ohne DOM), im Browser als `Logic`, in Node per require. */
(function (root) {
  const DAY = 86400000;

  const toDate = (iso) => new Date(iso + 'T00:00:00Z');
  const toIso = (d) => d.toISOString().slice(0, 10);
  const addDays = (iso, n) => toIso(new Date(toDate(iso).getTime() + n * DAY));
  const daysBetween = (a, b) => Math.round((toDate(b) - toDate(a)) / DAY);

  function nextDue(due, repeat) {
    if (!due) return null;
    if (repeat === 'weekly') return addDays(due, 7);
    if (repeat === 'monthly') {
      const d = toDate(due);
      const day = d.getUTCDate();
      const first = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1));
      const last = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
      first.setUTCDate(Math.min(day, last));
      return toIso(first);
    }
    return null;
  }

  function weekDays(today) {
    const dow = (toDate(today).getUTCDay() + 6) % 7; // Mo = 0
    const monday = addDays(today, -dow);
    return Array.from({ length: 7 }, (_, i) => addDays(monday, i));
  }

  function dueLabel(due, today) {
    if (!due) return '';
    const n = daysBetween(today, due);
    if (n === 0) return 'heute';
    if (n === 1) return 'morgen';
    if (n > 1) return `in ${n} Tagen`;
    const k = -n;
    return `überfällig seit ${k} ${k === 1 ? 'Tag' : 'Tagen'}`;
  }

  function rankOf(t, today) {
    if (t.due && t.due < today) return 0;
    if (t.due) return 1;
    if (t.status === 'doing') return 2;
    return 3;
  }

  function rank(tasks, today, skip) {
    const open = tasks.filter((t) => t.status !== 'done');
    const skipped = new Set(skip || []);
    const usable = open.filter((t) => !skipped.has(t.id));
    const list = usable.length ? usable : open;
    return list.slice().sort((a, b) => {
      const ra = rankOf(a, today);
      const rb = rankOf(b, today);
      if (ra !== rb) return ra - rb;
      if (a.due && b.due && a.due !== b.due) return a.due < b.due ? -1 : 1;
      if ((a.status === 'doing') !== (b.status === 'doing')) return a.status === 'doing' ? -1 : 1;
      return (a.createdAt || 0) - (b.createdAt || 0);
    });
  }

  function reasonFor(t, today) {
    if (t.due) return dueLabel(t.due, today).replace(/^(heute|morgen|in )/, (m) => 'Frist: ' + m);
    if (t.status === 'doing') return 'Du bist schon dran';
    return 'Schon länger offen';
  }

  function pickNext(tasks, today, skip) {
    const task = rank(tasks, today, skip)[0];
    if (!task) return null;
    const step = (task.steps || []).find((s) => !s.done) || null;
    return { task, step, reason: reasonFor(task, today) };
  }

  function mergeData(local, incoming) {
    if (!incoming || !Array.isArray(incoming.tasks)) throw new Error('Keine gültige Zentrale-Datei');
    const byId = new Map((local.tasks || []).map((t) => [t.id, t]));
    for (const t of incoming.tasks) {
      if (!t || typeof t.id !== 'string' || typeof t.title !== 'string') throw new Error('Aufgabe ungültig');
      const mine = byId.get(t.id);
      if (!mine || (t.updatedAt || 0) > (mine.updatedAt || 0)) byId.set(t.id, t);
    }
    return { ...local, tasks: [...byId.values()] };
  }

  const api = { toIso, addDays, daysBetween, nextDue, weekDays, dueLabel, rank, pickNext, mergeData };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Logic = api;
})(typeof self !== 'undefined' ? self : this);
