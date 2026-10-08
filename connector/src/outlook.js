import fs from "node:fs";
import { PublicClientApplication } from "@azure/msal-node";
import { MSAL_CACHE_FILE, ensureConfigDir, readConfig } from "./config.js";

// "consumers" = private Microsoft accounts (outlook.com, hotmail.com, live.com).
const AUTHORITY = "https://login.microsoftonline.com/consumers";
export const SCOPES = ["User.Read", "Mail.ReadWrite", "Mail.Send"];
const GRAPH = "https://graph.microsoft.com/v1.0";

const cachePlugin = {
  async beforeCacheAccess(ctx) {
    if (fs.existsSync(MSAL_CACHE_FILE)) {
      ctx.tokenCache.deserialize(fs.readFileSync(MSAL_CACHE_FILE, "utf8"));
    }
  },
  async afterCacheAccess(ctx) {
    if (ctx.cacheHasChanged) {
      ensureConfigDir();
      fs.writeFileSync(MSAL_CACHE_FILE, ctx.tokenCache.serialize(), { mode: 0o600 });
    }
  },
};

export function createMsalApp() {
  const { msClientId } = readConfig();
  if (!msClientId) {
    throw new Error("Outlook ist noch nicht eingerichtet. Bitte im Terminal 'npm run setup' ausführen.");
  }
  return new PublicClientApplication({
    auth: { clientId: msClientId, authority: AUTHORITY },
    cache: { cachePlugin },
  });
}

async function getToken() {
  const app = createMsalApp();
  const [account] = await app.getTokenCache().getAllAccounts();
  if (!account) {
    throw new Error("Nicht bei Microsoft angemeldet. Bitte im Terminal 'npm run login' ausführen.");
  }
  const result = await app.acquireTokenSilent({ account, scopes: SCOPES });
  return result.accessToken;
}

async function graph(method, urlPath, body) {
  const token = await getToken();
  const res = await fetch(urlPath.startsWith("http") ? urlPath : GRAPH + urlPath, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Prefer: 'outlook.body-content-type="text"',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(`Microsoft Graph Fehler ${res.status}: ${await res.text()}`);
  }
  if (res.status === 202 || res.status === 204) return null;
  return res.json();
}

const LIST_FIELDS = "id,subject,from,receivedDateTime,isRead,importance,bodyPreview,hasAttachments";

function slim(m) {
  return {
    id: m.id,
    betreff: m.subject,
    von: m.from?.emailAddress ? `${m.from.emailAddress.name} <${m.from.emailAddress.address}>` : undefined,
    empfangen: m.receivedDateTime,
    gelesen: m.isRead,
    wichtig: m.importance === "high",
    anhang: m.hasAttachments,
    vorschau: m.bodyPreview,
  };
}

const recipients = (list = []) => list.map((address) => ({ emailAddress: { address } }));

export async function listMessages({ folder = "inbox", top = 20, unreadOnly = false }) {
  const params = new URLSearchParams({
    $top: String(top),
    $select: LIST_FIELDS,
    $orderby: "receivedDateTime desc",
  });
  if (unreadOnly) params.set("$filter", "isRead eq false");
  const data = await graph("GET", `/me/mailFolders/${encodeURIComponent(folder)}/messages?${params}`);
  return data.value.map(slim);
}

export async function searchMessages({ query, top = 20 }) {
  const params = new URLSearchParams({
    $search: `"${query.replace(/"/g, "")}"`,
    $top: String(top),
    $select: LIST_FIELDS,
  });
  const data = await graph("GET", `/me/messages?${params}`);
  return data.value.map(slim);
}

export async function getMessage({ id }) {
  const m = await graph(
    "GET",
    `/me/messages/${encodeURIComponent(id)}?$select=${LIST_FIELDS},toRecipients,ccRecipients,body`,
  );
  return {
    ...slim(m),
    an: m.toRecipients?.map((r) => r.emailAddress.address),
    cc: m.ccRecipients?.map((r) => r.emailAddress.address),
    inhalt: m.body?.content,
  };
}

function buildMessage({ to, cc, subject, body }) {
  return {
    subject,
    body: { contentType: "Text", content: body },
    toRecipients: recipients(to),
    ccRecipients: recipients(cc),
  };
}

export async function sendMail(args) {
  await graph("POST", "/me/sendMail", { message: buildMessage(args), saveToSentItems: true });
  return { gesendet: true };
}

export async function createDraft(args) {
  const draft = await graph("POST", "/me/messages", buildMessage(args));
  return { entwurfId: draft.id, link: draft.webLink };
}

export async function reply({ id, body, replyAll = false, sendNow = false }) {
  const action = replyAll ? "createReplyAll" : "createReply";
  const draft = await graph("POST", `/me/messages/${encodeURIComponent(id)}/${action}`, {
    comment: body,
  });
  if (sendNow) {
    await graph("POST", `/me/messages/${encodeURIComponent(draft.id)}/send`);
    return { gesendet: true };
  }
  return { entwurfId: draft.id, link: draft.webLink };
}

export async function markRead({ id, isRead = true }) {
  await graph("PATCH", `/me/messages/${encodeURIComponent(id)}`, { isRead });
  return { ok: true };
}

export async function moveMessage({ id, folder }) {
  const moved = await graph("POST", `/me/messages/${encodeURIComponent(id)}/move`, {
    destinationId: folder,
  });
  return { neueId: moved.id };
}

export async function deleteMessage({ id }) {
  // Moves to "Gelöschte Elemente", so it can still be restored.
  await graph("POST", `/me/messages/${encodeURIComponent(id)}/move`, {
    destinationId: "deleteditems",
  });
  return { geloescht: true };
}

export async function listFolders() {
  const data = await graph("GET", "/me/mailFolders?$top=100&$select=id,displayName,unreadItemCount,totalItemCount");
  return data.value.map((f) => ({
    id: f.id,
    name: f.displayName,
    ungelesen: f.unreadItemCount,
    gesamt: f.totalItemCount,
  }));
}
