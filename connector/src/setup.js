#!/usr/bin/env node
// Guided one-time setup: run with "npm run setup" (or "npm run login" for Microsoft only).
import readline from "node:readline/promises";
import { stdin, stdout } from "node:process";
import { readConfig, storeIcloudPassword, writeConfig } from "./config.js";
import { SCOPES, createMsalApp } from "./msal.js";
import { createLocalIcloud } from "./local.js";

const rl = readline.createInterface({ input: stdin, output: stdout });
const onlyLogin = process.argv.includes("--login");
const config = readConfig();

async function microsoft() {
  console.log("\n📧 Schritt 1: Outlook");
  if (!config.msClientId || !onlyLogin) {
    const id = (await rl.question(`Anwendungs-ID (Client ID) von Microsoft${config.msClientId ? ` [${config.msClientId}]` : ""}: `)).trim();
    if (id) writeConfig({ msClientId: id });
  }
  const app = createMsalApp();
  const result = await app.acquireTokenByDeviceCode({
    scopes: SCOPES,
    deviceCodeCallback: (r) => {
      console.log(`\n👉 Öffne ${r.verificationUri} und gib diesen Code ein: ${r.userCode}\n`);
    },
  });
  console.log(`✅ Angemeldet als ${result.account.username}`);
}

async function apple() {
  console.log("\n📅 Schritt 2: Apple iCloud Kalender");
  const user = (await rl.question(`Apple-ID E-Mail${config.icloudUser ? ` [${config.icloudUser}]` : ""}: `)).trim() || config.icloudUser;
  const password = (await rl.question("App-spezifisches Passwort (xxxx-xxxx-xxxx-xxxx): ")).trim();
  writeConfig({ icloudUser: user });
  storeIcloudPassword(user, password);
  const calendars = await createLocalIcloud().listCalendars();
  console.log(`✅ ${calendars.length} Kalender gefunden: ${calendars.map((c) => c.name).join(", ")}`);
}

try {
  await microsoft();
  if (!onlyLogin) await apple();
  console.log("\n🎉 Fertig. Jetzt Claude Desktop komplett beenden und neu starten.");
} catch (err) {
  console.error(`\n❌ ${err.message}`);
  process.exitCode = 1;
} finally {
  rl.close();
}
