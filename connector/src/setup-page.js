// Mobile friendly one-page setup (iPad / iPhone). Rendered by the Worker.
export function setupPage(mcpUrl) {
  return `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ADHS Assistant Einrichtung</title>
<style>
  :root { --bg:#f6f5f2; --card:#fff; --text:#1d1d1f; --muted:#6e6e73; --accent:#5b5bd6; --ok:#2e8b57; --err:#c0392b; --line:#e3e1dc; }
  @media (prefers-color-scheme: dark) { :root { --bg:#141416; --card:#1e1e22; --text:#f2f2f2; --muted:#a1a1a6; --accent:#8b8bf0; --ok:#5cc98a; --err:#ff7b6b; --line:#2f2f35; } }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font:17px/1.5 -apple-system, system-ui, sans-serif; }
  main { max-width:560px; margin:0 auto; padding:24px 16px 64px; }
  h1 { font-size:26px; margin:0 0 4px; }
  p.lead { color:var(--muted); margin:0 0 24px; }
  section { background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px; margin-bottom:16px; }
  h2 { font-size:19px; margin:0 0 8px; display:flex; gap:8px; align-items:center; }
  .badge { margin-left:auto; font-size:14px; font-weight:600; color:var(--muted); }
  .badge.ok { color:var(--ok); }
  ol { padding-left:20px; margin:8px 0 16px; }
  label { display:block; font-weight:600; margin:12px 0 4px; }
  input { width:100%; font-size:17px; padding:12px; border-radius:10px; border:1px solid var(--line); background:var(--bg); color:var(--text); }
  button { width:100%; margin-top:16px; padding:14px; font-size:17px; font-weight:600; border:0; border-radius:12px; background:var(--accent); color:#fff; }
  button:disabled { opacity:.5; }
  .msg { margin-top:12px; font-weight:600; }
  .msg.ok { color:var(--ok); } .msg.err { color:var(--err); }
  .code { font:700 28px/1.2 ui-monospace, monospace; letter-spacing:3px; text-align:center; padding:12px; border:2px dashed var(--accent); border-radius:12px; margin:12px 0; }
  .url { word-break:break-all; font:15px ui-monospace, monospace; padding:12px; background:var(--bg); border-radius:10px; }
  a { color:var(--accent); }
</style>
</head>
<body>
<main>
  <h1>🧠 ADHS Assistant</h1>
  <p class="lead">3 Schritte. Ca. <b>15 Minuten</b>. Alles am iPad.</p>

  <section>
    <h2>📅 1. Apple Kalender <span class="badge" id="b-icloud">offen</span></h2>
    <ol>
      <li><a href="https://account.apple.com" target="_blank">account.apple.com</a> öffnen</li>
      <li><b>Anmeldung und Sicherheit</b> → <b>App-spezifische Passwörter</b> → <b>+</b></li>
      <li>Name <b>Claude</b>, Passwort kopieren</li>
    </ol>
    <label for="user">Apple-ID (E-Mail)</label>
    <input id="user" type="email" autocomplete="username">
    <label for="pw">App-Passwort</label>
    <input id="pw" type="password" placeholder="xxxx-xxxx-xxxx-xxxx" autocomplete="off">
    <button id="btn-icloud">Kalender verbinden</button>
    <div class="msg" id="m-icloud"></div>
  </section>

  <section>
    <h2>📧 2. Outlook <span class="badge" id="b-ms">offen</span></h2>
    <ol>
      <li><a href="https://entra.microsoft.com" target="_blank">entra.microsoft.com</a> öffnen, mit Outlook anmelden</li>
      <li><b>App-Registrierungen</b> → <b>Neue Registrierung</b>, Name <b>ADHS Assistant</b></li>
      <li>Kontotyp: <b>Nur persönliche Microsoft-Konten</b> → <b>Registrieren</b></li>
      <li><b>Authentifizierung</b> → <b>Öffentliche Clientflows zulassen: Ja</b> → Speichern</li>
      <li><b>Anwendungs-ID (Client-ID)</b> kopieren</li>
    </ol>
    <label for="cid">Anwendungs-ID (Client-ID)</label>
    <input id="cid" autocomplete="off" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx">
    <button id="btn-ms">Outlook verbinden</button>
    <div id="ms-code" hidden>
      <p>👉 Öffne <a id="ms-link" target="_blank"></a> und gib diesen Code ein:</p>
      <div class="code" id="ms-usercode"></div>
      <p>Danach hierher zurückkommen. Die Seite erkennt es automatisch. ⏳</p>
    </div>
    <div class="msg" id="m-ms"></div>
  </section>

  <section>
    <h2>🔌 3. In Claude eintragen <span class="badge" id="b-claude">zuletzt</span></h2>
    <ol>
      <li>In Claude: <b>Einstellungen</b> → <b>Connectors</b> → <b>Eigenen Connector hinzufügen</b></li>
      <li>Name: <b>ADHS Assistant</b></li>
      <li>Diese URL einfügen (geheim halten 🔒):</li>
    </ol>
    <div class="url" id="mcp-url">${mcpUrl}</div>
    <button id="btn-copy">URL kopieren</button>
    <div class="msg" id="m-copy"></div>
  </section>
</main>
<script>
  const base = location.pathname.replace(/\\/$/, "");
  const $ = (id) => document.getElementById(id);
  async function api(action, body) {
    const res = await fetch(base + "/" + action, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Fehler");
    return data;
  }
  function msg(id, text, ok) { const el = $(id); el.textContent = text; el.className = "msg " + (ok ? "ok" : "err"); }
  function badge(id, done) { const el = $(id); el.textContent = done ? "✅ fertig" : "offen"; el.className = "badge" + (done ? " ok" : ""); }

  async function refresh() {
    const s = await api("status");
    badge("b-icloud", s.icloud); badge("b-ms", s.outlook);
    if (s.icloudUser) $("user").value = s.icloudUser;
  }

  $("btn-icloud").onclick = async () => {
    $("btn-icloud").disabled = true; msg("m-icloud", "⏳ Verbinde…", true);
    try {
      const r = await api("icloud", { user: $("user").value, password: $("pw").value });
      msg("m-icloud", "✅ Verbunden: " + r.calendars.join(", "), true); $("pw").value = ""; badge("b-icloud", true);
    } catch (e) { msg("m-icloud", "❌ " + e.message, false); }
    $("btn-icloud").disabled = false;
  };

  $("btn-ms").onclick = async () => {
    $("btn-ms").disabled = true; $("m-ms").textContent = "";
    try {
      const r = await api("ms-start", { clientId: $("cid").value });
      $("ms-link").href = r.verificationUri; $("ms-link").textContent = r.verificationUri;
      $("ms-usercode").textContent = r.userCode; $("ms-code").hidden = false;
      const poll = async () => {
        try {
          const p = await api("ms-poll", { deviceCode: r.deviceCode });
          if (p.done) { $("ms-code").hidden = true; msg("m-ms", "✅ Outlook verbunden", true); badge("b-ms", true); $("btn-ms").disabled = false; return; }
          setTimeout(poll, (r.interval || 5) * 1000);
        } catch (e) { $("ms-code").hidden = true; msg("m-ms", "❌ " + e.message, false); $("btn-ms").disabled = false; }
      };
      setTimeout(poll, (r.interval || 5) * 1000);
    } catch (e) { msg("m-ms", "❌ " + e.message, false); $("btn-ms").disabled = false; }
  };

  $("btn-copy").onclick = async () => {
    try { await navigator.clipboard.writeText($("mcp-url").textContent); msg("m-copy", "✅ Kopiert", true); }
    catch { msg("m-copy", "Bitte die URL lange drücken und kopieren.", false); }
  };

  refresh().catch(() => {});
</script>
</body>
</html>`;
}
