import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const CONFIG_DIR = path.join(os.homedir(), ".adhs-assistant");
export const CONFIG_FILE = path.join(CONFIG_DIR, "config.json");
export const MSAL_CACHE_FILE = path.join(CONFIG_DIR, "msal-cache.json");
export const KEYCHAIN_SERVICE = "adhs-assistant-icloud";

export function ensureConfigDir() {
  fs.mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
}

export function readConfig() {
  let fileConfig = {};
  if (fs.existsSync(CONFIG_FILE)) {
    fileConfig = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"));
  }
  return {
    msClientId: process.env.MS_CLIENT_ID || fileConfig.msClientId,
    icloudUser: process.env.ICLOUD_USER || fileConfig.icloudUser,
  };
}

export function writeConfig(patch) {
  ensureConfigDir();
  const current = fs.existsSync(CONFIG_FILE)
    ? JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"))
    : {};
  fs.writeFileSync(CONFIG_FILE, JSON.stringify({ ...current, ...patch }, null, 2), {
    mode: 0o600,
  });
}

// The iCloud app-specific password lives in the macOS Keychain, never in a plain file.
export function readIcloudPassword(user) {
  if (process.env.ICLOUD_APP_PASSWORD) return process.env.ICLOUD_APP_PASSWORD;
  try {
    return execFileSync(
      "security",
      ["find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", user, "-w"],
      { encoding: "utf8" },
    ).trim();
  } catch {
    return undefined;
  }
}

export function storeIcloudPassword(user, password) {
  execFileSync("security", [
    "add-generic-password",
    "-U",
    "-s",
    KEYCHAIN_SERVICE,
    "-a",
    user,
    "-w",
    password,
  ]);
}
