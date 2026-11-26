// "Berg zerlegen": fragt Claude nach kleinen Schritten für eine Aufgabe (für die Zentrale-PWA).
const MODEL = "claude-haiku-5-5";
const DEFAULT_DAILY_LIMIT = 100;

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};
const reply = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...CORS } });

const SYSTEM = `Du hilfst einer Person mit ADHS, eine Aufgabe in kleine Schritte zu zerlegen.
Regeln:
- 3 bis 7 Schritte, jeder ein einzelner, konkreter Handgriff (Verb am Anfang, deutsch, max. 90 Zeichen).
- Der erste Schritt ist winzig (höchstens 5 Minuten) und sofort machbar, z. B. "Datei öffnen und Titel tippen".
- Jeder Schritt dauert 5, 10 oder 20 Minuten.
- Keine Motivationssprüche, keine Erklärungen.
Antworte NUR mit JSON: {"steps":[{"text":"...","min":5}]}`;

export function readInput(body) {
  const title = String(body?.title ?? "").trim().slice(0, 120);
  if (!title) throw new Error("Bitte einen Titel angeben.");
  const notes = String(body?.notes ?? "").trim().slice(0, 500);
  return { title, notes };
}

export function parseSteps(raw) {
  const start = String(raw).indexOf("{");
  const end = String(raw).lastIndexOf("}");
  if (start < 0 || end < start) throw new Error("Keine Schritte erkannt.");
  const data = JSON.parse(String(raw).slice(start, end + 1));
  const toMin = (m) => (Number(m) <= 7 ? 5 : Number(m) <= 14 ? 10 : 20);
  const steps = (Array.isArray(data.steps) ? data.steps : [])
    .map((s) => ({ text: String(s?.text ?? "").trim().slice(0, 120), min: toMin(s?.min) }))
    .filter((s) => s.text)
    .slice(0, 8);
  if (!steps.length) throw new Error("Keine Schritte erkannt.");
  return steps;
}

async function underLimit(env) {
  const limit = Number(env.SPLIT_DAILY_LIMIT) || DEFAULT_DAILY_LIMIT;
  const key = `split_count:${new Date().toISOString().slice(0, 10)}`;
  const used = Number(await env.STORE.get(key)) || 0;
  if (used >= limit) return false;
  await env.STORE.put(key, String(used + 1), { expirationTtl: 172800 });
  return true;
}

export async function handleSplit(request, env, fetchImpl = fetch) {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (request.method !== "POST") return reply({ error: "Nur POST erlaubt." }, 405);
  // Also accept ANTHROPIC_API_KEY_2 etc.: Cloudflare forces a new name if the plain one is taken.
  const apiKey = Object.keys(env).filter((k) => k.startsWith("ANTHROPIC_API_KEY")).sort()
    .map((k) => env[k]).find((v) => typeof v === "string" && v.trim());
  if (!apiKey) {
    return reply({ error: "Noch kein API-Key im Server eingetragen (ANTHROPIC_API_KEY)." }, 503);
  }

  let input;
  try {
    input = readInput(await request.json());
  } catch (err) {
    return reply({ error: err.message }, 400);
  }
  if (!(await underLimit(env))) return reply({ error: "Tageslimit erreicht. Morgen geht es wieder." }, 429);

  try {
    const res = await fetchImpl("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": apiKey.trim(), "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 600,
        system: SYSTEM,
        messages: [{ role: "user", content: `Aufgabe: ${input.title}${input.notes ? `\nNotiz: ${input.notes}` : ""}` }],
      }),
    });
    if (!res.ok) return reply({ error: `Claude antwortet gerade nicht (${res.status}).` }, 502);
    const data = await res.json();
    const text = (data.content || []).filter((c) => c.type === "text").map((c) => c.text).join("");
    return reply({ steps: parseSteps(text) });
  } catch (err) {
    return reply({ error: "Die Antwort von Claude war nicht lesbar. Bitte nochmal versuchen." }, 502);
  }
}
