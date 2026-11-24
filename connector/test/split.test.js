import test from "node:test";
import assert from "node:assert/strict";
import { parseSteps, readInput, handleSplit } from "../src/split.js";

const kv = () => {
  const m = new Map();
  return { get: async (k) => m.get(k) ?? null, put: async (k, v) => void m.set(k, v) };
};
const post = (body) => new Request("https://x/split/k", { method: "POST", body: JSON.stringify(body) });
const claude = (text, ok = true) => async () =>
  new Response(JSON.stringify({ content: [{ type: "text", text }] }), { status: ok ? 200 : 500 });

test("parseSteps: JSON im Codeblock, min auf 5/10/20, max. 8 Schritte, leere raus", () => {
  const raw = '```json\n{"steps":[{"text":"Datei öffnen","min":3},{"text":" ","min":10},{"text":"Titel tippen","min":15},{"text":"Lang","min":99}]}\n```';
  assert.deepEqual(parseSteps(raw), [
    { text: "Datei öffnen", min: 5 },
    { text: "Titel tippen", min: 20 },
    { text: "Lang", min: 20 },
  ]);
  const many = JSON.stringify({ steps: Array.from({ length: 12 }, (_, i) => ({ text: `s${i}`, min: 10 })) });
  assert.equal(parseSteps(many).length, 8);
});

test("parseSteps: Müll wirft", () => {
  assert.throws(() => parseSteps("Hallo!"));
  assert.throws(() => parseSteps('{"steps":[]}'));
});

test("readInput: kürzt, trimmt, leerer Titel wirft", () => {
  assert.deepEqual(readInput({ title: "  Referat  ", notes: "x".repeat(900) }).notes.length, 500);
  assert.equal(readInput({ title: "a".repeat(300) }).title.length, 120);
  assert.throws(() => readInput({ title: "   " }));
  assert.throws(() => readInput(null));
});

test("handleSplit: OPTIONS beantwortet Preflight mit CORS", async () => {
  const res = await handleSplit(new Request("https://x/split/k", { method: "OPTIONS" }), { STORE: kv() });
  assert.equal(res.status, 204);
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), "*");
});

test("handleSplit: ohne API-Key 503 mit deutscher Meldung", async () => {
  const res = await handleSplit(post({ title: "Referat" }), { STORE: kv() }, claude("{}"));
  assert.equal(res.status, 503);
  assert.match((await res.json()).error, /API-Key/);
});

test("handleSplit: Erfolg liefert Schritte", async () => {
  const res = await handleSplit(post({ title: "Referat" }), { STORE: kv(), ANTHROPIC_API_KEY: "sk" },
    claude('{"steps":[{"text":"Thema aufschreiben","min":5}]}'));
  assert.equal(res.status, 200);
  assert.deepEqual((await res.json()).steps, [{ text: "Thema aufschreiben", min: 5 }]);
});

test("handleSplit: Tageslimit greift (429) nach 2 Anfragen", async () => {
  const env = { STORE: kv(), ANTHROPIC_API_KEY: "sk", SPLIT_DAILY_LIMIT: "2" };
  const ok = claude('{"steps":[{"text":"a","min":5}]}');
  assert.equal((await handleSplit(post({ title: "t" }), env, ok)).status, 200);
  assert.equal((await handleSplit(post({ title: "t" }), env, ok)).status, 200);
  assert.equal((await handleSplit(post({ title: "t" }), env, ok)).status, 429);
});

test("handleSplit: Fehler der API wird zu 502, Titel leer zu 400", async () => {
  const env = { STORE: kv(), ANTHROPIC_API_KEY: "sk" };
  assert.equal((await handleSplit(post({ title: "t" }), env, claude("x", false))).status, 502);
  assert.equal((await handleSplit(post({ title: "" }), env, claude("{}"))).status, 400);
});
