// Cloud version for Cloudflare Workers: remote MCP endpoint + iPad friendly setup page.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { createIcloud } from "./icloud.js";
import { SCOPES, createOutlook } from "./outlook.js";
import { registerTools } from "./tools.js";
import { setupPage } from "./setup-page.js";

const MS_BASE = "https://login.microsoftonline.com/consumers/oauth2/v2.0";
const SCOPE = SCOPES.join(" ");

// Access token cache per Worker instance; the refresh token lives in KV.
let cachedToken;

async function keyMatches(given, expected) {
  if (!given || !expected) return false;
  const enc = new TextEncoder();
  const a = enc.encode(given);
  const b = enc.encode(expected);
  if (a.byteLength !== b.byteLength) return false;
  return crypto.subtle.timingSafeEqual(a, b);
}

async function msToken(form) {
  const res = await fetch(`${MS_BASE}/token`, { method: "POST", body: new URLSearchParams(form) });
  return { ok: res.ok, data: await res.json() };
}

async function getMicrosoftToken(env) {
  if (cachedToken && cachedToken.expires > Date.now() + 60_000) return cachedToken.value;
  const [clientId, refreshToken] = await Promise.all([
    env.STORE.get("ms_client_id"),
    env.STORE.get("ms_refresh_token"),
  ]);
  if (!clientId || !refreshToken) {
    throw new Error("Outlook ist noch nicht verbunden. Bitte die Einrichtungsseite öffnen.");
  }
  const { ok, data } = await msToken({
    client_id: clientId,
    grant_type: "refresh_token",
    refresh_token: refreshToken,
    scope: SCOPE,
  });
  if (!ok) {
    throw new Error(`Microsoft Anmeldung abgelaufen (${data.error}). Bitte auf der Einrichtungsseite neu verbinden.`);
  }
  if (data.refresh_token && data.refresh_token !== refreshToken) {
    await env.STORE.put("ms_refresh_token", data.refresh_token);
  }
  cachedToken = { value: data.access_token, expires: Date.now() + data.expires_in * 1000 };
  return cachedToken.value;
}

function services(env) {
  const outlook = createOutlook({ getToken: () => getMicrosoftToken(env) });
  const icloud = createIcloud({
    timeZone: env.TIMEZONE || "Europe/Berlin",
    getCredentials: async () => ({
      user: await env.STORE.get("icloud_user"),
      password: await env.STORE.get("icloud_password"),
    }),
  });
  return { outlook, icloud };
}

async function handleMcp(request, env) {
  const { outlook, icloud } = services(env);
  const server = new McpServer({ name: "adhs-assistant", version: "1.0.0" });
  registerTools(server, { outlook: () => outlook, icloud: () => icloud });
  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });
  await server.connect(transport);
  return transport.handleRequest(request);
}

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

async function handleSetupApi(action, request, env) {
  const body = await request.json().catch(() => ({}));

  if (action === "status") {
    const [ms, user, pw] = await Promise.all([
      env.STORE.get("ms_refresh_token"),
      env.STORE.get("icloud_user"),
      env.STORE.get("icloud_password"),
    ]);
    return json({ outlook: Boolean(ms), icloud: Boolean(user && pw), icloudUser: user });
  }

  if (action === "icloud") {
    const user = String(body.user || "").trim();
    const password = String(body.password || "").trim();
    if (!user || !password) return json({ error: "Bitte Apple-ID und App-Passwort eingeben." }, 400);
    const icloud = createIcloud({ timeZone: env.TIMEZONE, getCredentials: async () => ({ user, password }) });
    try {
      const calendars = await icloud.listCalendars();
      await env.STORE.put("icloud_user", user);
      await env.STORE.put("icloud_password", password);
      return json({ calendars: calendars.map((c) => c.name) });
    } catch (err) {
      return json({ error: `Anmeldung bei iCloud fehlgeschlagen: ${err.message}` }, 400);
    }
  }

  if (action === "ms-start") {
    const clientId = String(body.clientId || "").trim();
    if (!clientId) return json({ error: "Bitte die Anwendungs-ID (Client-ID) eingeben." }, 400);
    const res = await fetch(`${MS_BASE}/devicecode`, {
      method: "POST",
      body: new URLSearchParams({ client_id: clientId, scope: SCOPE }),
    });
    const data = await res.json();
    if (!res.ok) return json({ error: data.error_description || data.error }, 400);
    await env.STORE.put("ms_client_id", clientId);
    return json({
      userCode: data.user_code,
      verificationUri: data.verification_uri,
      deviceCode: data.device_code,
      interval: data.interval,
    });
  }

  if (action === "ms-poll") {
    const clientId = await env.STORE.get("ms_client_id");
    const { ok, data } = await msToken({
      client_id: clientId,
      grant_type: "urn:ietf:params:oauth:grant-type:device_code",
      device_code: String(body.deviceCode || ""),
    });
    if (ok) {
      await env.STORE.put("ms_refresh_token", data.refresh_token);
      cachedToken = undefined;
      return json({ done: true });
    }
    if (data.error === "authorization_pending" || data.error === "slow_down") return json({ pending: true });
    return json({ error: data.error_description || data.error }, 400);
  }

  return json({ error: "Unbekannte Aktion" }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const [, area, key, action] = url.pathname.split("/");

    if (!env.ACCESS_KEY) {
      return new Response(
        "Fast fertig: Bitte in Cloudflare unter Einstellungen > Variablen und Geheimnisse ein Secret ACCESS_KEY anlegen.",
        { status: 500, headers: { "Content-Type": "text/plain; charset=utf-8" } },
      );
    }
    if (area !== "mcp" && area !== "setup") {
      return new Response("ADHS Assistant Connector läuft ✅", {
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    }
    if (!(await keyMatches(key, env.ACCESS_KEY))) return new Response("Nicht erlaubt", { status: 403 });

    if (area === "mcp") {
      // Stateless server: no long-lived SSE stream, only POST requests.
      if (request.method !== "POST") {
        return new Response("Method Not Allowed", { status: 405, headers: { Allow: "POST" } });
      }
      return handleMcp(request, env);
    }
    if (!action && request.method === "GET") {
      return new Response(setupPage(`${url.origin}/mcp/${key}`), {
        headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
      });
    }
    if (request.method === "POST") return handleSetupApi(action, request, env);
    return new Response("Nicht gefunden", { status: 404 });
  },
};
