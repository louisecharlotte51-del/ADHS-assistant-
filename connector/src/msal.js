import fs from "node:fs";
import { PublicClientApplication } from "@azure/msal-node";
import { MSAL_CACHE_FILE, ensureConfigDir, readConfig } from "./config.js";

// "consumers" = private Microsoft accounts (outlook.com, hotmail.com, live.com).
const AUTHORITY = "https://login.microsoftonline.com/consumers";
export const SCOPES = ["User.Read", "Mail.ReadWrite", "Mail.Send"];

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

export async function getToken() {
  const app = createMsalApp();
  const [account] = await app.getTokenCache().getAllAccounts();
  if (!account) {
    throw new Error("Nicht bei Microsoft angemeldet. Bitte im Terminal 'npm run login' ausführen.");
  }
  const result = await app.acquireTokenSilent({ account, scopes: SCOPES });
  return result.accessToken;
}
