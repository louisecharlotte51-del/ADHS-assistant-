'use strict';
process.env.TZ = 'Europe/Berlin';
const test = require('node:test');
const assert = require('node:assert/strict');
const L = require('../logic.js');

const T = (o) => ({ id: o.id, area: 'uni', title: 't', status: 'todo', steps: [], createdAt: 1, updatedAt: 1, ...o });
const TODAY = '2026-11-23'; // Montag

test('pickNext: leere Liste ergibt null', () => {
  assert.equal(L.pickNext([], TODAY), null);
  assert.equal(L.pickNext([T({ id: 'a', status: 'done' })], TODAY), null);
});

test('pickNext: überfällig schlägt zukünftige Frist', () => {
  const r = L.pickNext([T({ id: 'a', due: '2026-11-25' }), T({ id: 'b', due: '2026-11-20' })], TODAY);
  assert.equal(r.task.id, 'b');
  assert.match(r.reason, /überfällig/);
});

test('pickNext: Frist schlägt doing, doing schlägt älteste', () => {
  const tasks = [T({ id: 'old', createdAt: 1 }), T({ id: 'doing', status: 'doing', createdAt: 5 }), T({ id: 'due', due: '2026-12-01', createdAt: 9 })];
  assert.deepEqual(L.rank(tasks, TODAY).map((t) => t.id), ['due', 'doing', 'old']);
});

test('pickNext: erster unerledigter Schritt, sonst step null (ohne Schritte, ohne Frist)', () => {
  const withSteps = T({ id: 'a', steps: [{ id: 's1', text: 'x', min: 5, done: true }, { id: 's2', text: 'y', min: 10, done: false }] });
  assert.equal(L.pickNext([withSteps], TODAY).step.id, 's2');
  const bare = L.pickNext([T({ id: 'b' })], TODAY);
  assert.equal(bare.step, null);
  assert.equal(bare.task.id, 'b');
});

test('pickNext: skip überspringt, ignoriert skip wenn alles übersprungen', () => {
  const tasks = [T({ id: 'a', due: '2026-11-20' }), T({ id: 'b' })];
  assert.equal(L.pickNext(tasks, TODAY, ['a']).task.id, 'b');
  assert.equal(L.pickNext(tasks, TODAY, ['a', 'b']).task.id, 'a');
});

test('nextDue: weekly und monthly mit Monatsende-Klemmung', () => {
  assert.equal(L.nextDue('2026-11-23', 'weekly'), '2026-11-30');
  assert.equal(L.nextDue('2026-01-31', 'monthly'), '2026-02-28');
  assert.equal(L.nextDue('2026-12-15', 'monthly'), '2027-01-15');
  assert.equal(L.nextDue('2026-11-23', undefined), null);
});

test('weekDays: Montag bis Sonntag', () => {
  assert.deepEqual(L.weekDays('2026-11-25'), ['2026-11-23', '2026-11-24', '2026-11-25', '2026-11-26', '2026-11-27', '2026-11-28', '2026-11-29']);
  assert.equal(L.weekDays('2026-11-29')[0], '2026-11-23'); // Sonntag gehört zur Woche davor
});

test('dueLabel', () => {
  assert.equal(L.dueLabel('2026-11-23', TODAY), 'heute');
  assert.equal(L.dueLabel('2026-11-24', TODAY), 'morgen');
  assert.equal(L.dueLabel('2026-11-26', TODAY), 'in 3 Tagen');
  assert.equal(L.dueLabel('2026-11-22', TODAY), 'überfällig seit 1 Tag');
  assert.equal(L.dueLabel('2026-11-20', TODAY), 'überfällig seit 3 Tagen');
  assert.equal(L.dueLabel(undefined, TODAY), '');
});

test('mergeData: neueres updatedAt gewinnt, neue Aufgaben kommen dazu', () => {
  const local = { tasks: [T({ id: 'a', title: 'alt', updatedAt: 1 }), T({ id: 'b', updatedAt: 1 })] };
  const incoming = { tasks: [T({ id: 'a', title: 'neu', updatedAt: 2 }), T({ id: 'c', updatedAt: 1 })] };
  const m = L.mergeData(local, incoming);
  assert.equal(m.tasks.length, 3);
  assert.equal(m.tasks.find((t) => t.id === 'a').title, 'neu');
});

test('mergeData: kaputte Datei wirft, lokale Daten bleiben unverändert', () => {
  const local = { tasks: [T({ id: 'a' })] };
  assert.throws(() => L.mergeData(local, { foo: 1 }));
  assert.throws(() => L.mergeData(local, null));
  assert.equal(local.tasks.length, 1);
});

test('splitEndpoint: leitet die Zerlegen-Adresse aus Connector-/Einrichtungs-Link ab', () => {
  assert.equal(L.splitEndpoint('https://adhs-assistant.x.workers.dev/mcp/abc123'), 'https://adhs-assistant.x.workers.dev/split/abc123');
  assert.equal(L.splitEndpoint(' https://a.dev//setup/abc123/ '), 'https://a.dev/split/abc123');
  assert.equal(L.splitEndpoint('https://a.dev/split/k'), 'https://a.dev/split/k');
});

test('splitEndpoint: ungültige Eingaben ergeben null', () => {
  assert.equal(L.splitEndpoint(''), null);
  assert.equal(L.splitEndpoint('kein link'), null);
  assert.equal(L.splitEndpoint('https://a.dev/'), null);
  assert.equal(L.splitEndpoint('http://a.dev/mcp/k'), null);
});

test('splitEndpoint: verzeiht Text drumherum und fehlendes https://', () => {
  assert.equal(L.splitEndpoint('URL: https://a.dev/mcp/k123 kopiert'), 'https://a.dev/split/k123');
  assert.equal(L.splitEndpoint('adhs-assistant.x.workers.dev/setup/k123'), 'https://adhs-assistant.x.workers.dev/split/k123');
  assert.equal(L.splitEndpoint('https://a.dev/mcp/k123.'), 'https://a.dev/split/k123');
  assert.equal(L.splitEndpoint('https://adhs-assistant.x.workers.dev'), null);
});

test('Kalender: Tag, Sortierung, nächster Termin', () => {
  const ev = [
    { titel: 'Seminar', startIso: '2026-11-23T13:00:00.000Z', ganztaegig: false },
    { titel: 'Spät', startIso: '2026-11-23T23:30:00.000Z', ganztaegig: false }, // 00:30 Berlin = 24.11.
    { titel: 'Feiertag', startIso: '2026-11-23T00:00:00.000Z', ganztaegig: true },
    { titel: 'Früh', startIso: '2026-11-23T08:00:00.000Z', ganztaegig: false },
  ];
  assert.deepEqual(L.eventsOn(ev, '2026-11-23').map((e) => e.titel), ['Feiertag', 'Früh', 'Seminar']);
  assert.deepEqual(L.eventsOn(ev, '2026-11-24').map((e) => e.titel), ['Spät']);
  assert.equal(L.nextEvent(ev, Date.parse('2026-11-23T09:00:00Z')).titel, 'Seminar');
  assert.equal(L.nextEvent(ev, Date.parse('2026-11-25T09:00:00Z')), null);
  assert.deepEqual(L.eventsOn(undefined, '2026-11-23'), []);
});
