const GRAPH = "https://graph.microsoft.com/v1.0";
export const SCOPES = ["offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send"];
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

function buildMessage({ to, cc, subject, body }) {
  return {
    subject,
    body: { contentType: "Text", content: body },
    toRecipients: recipients(to),
    ccRecipients: recipients(cc),
  };
}

/** getToken() must resolve to a Microsoft Graph access token for the user. */
export function createOutlook({ getToken }) {
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

  async function listMessages({ folder = "inbox", top = 20, unreadOnly = false }) {
    const params = new URLSearchParams({
      $top: String(top),
      $select: LIST_FIELDS,
      $orderby: "receivedDateTime desc",
    });
    if (unreadOnly) params.set("$filter", "isRead eq false");
    const data = await graph("GET", `/me/mailFolders/${encodeURIComponent(folder)}/messages?${params}`);
    return data.value.map(slim);
  }

  async function searchMessages({ query, top = 20 }) {
    const params = new URLSearchParams({
      $search: `"${query.replace(/"/g, "")}"`,
      $top: String(top),
      $select: LIST_FIELDS,
    });
    const data = await graph("GET", `/me/messages?${params}`);
    return data.value.map(slim);
  }

  async function getMessage({ id }) {
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

  async function sendMail(args) {
    await graph("POST", "/me/sendMail", { message: buildMessage(args), saveToSentItems: true });
    return { gesendet: true };
  }

  async function createDraft(args) {
    const draft = await graph("POST", "/me/messages", buildMessage(args));
    return { entwurfId: draft.id, link: draft.webLink };
  }

  async function reply({ id, body, replyAll = false, sendNow = false }) {
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

  async function markRead({ id, isRead = true }) {
    await graph("PATCH", `/me/messages/${encodeURIComponent(id)}`, { isRead });
    return { ok: true };
  }

  async function moveMessage({ id, folder }) {
    const moved = await graph("POST", `/me/messages/${encodeURIComponent(id)}/move`, {
      destinationId: folder,
    });
    return { neueId: moved.id };
  }

  async function deleteMessage({ id }) {
    // Moves to "Gelöschte Elemente", so it can still be restored.
    await graph("POST", `/me/messages/${encodeURIComponent(id)}/move`, {
      destinationId: "deleteditems",
    });
    return { geloescht: true };
  }

  async function listFolders() {
    const data = await graph("GET", "/me/mailFolders?$top=100&$select=id,displayName,unreadItemCount,totalItemCount");
    return data.value.map((f) => ({
      id: f.id,
      name: f.displayName,
      ungelesen: f.unreadItemCount,
      gesamt: f.totalItemCount,
    }));
  }

  return { listMessages, searchMessages, getMessage, sendMail, createDraft, reply, markRead, moveMessage, deleteMessage, listFolders };
}
