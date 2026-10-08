import { readConfig, readIcloudPassword } from "./config.js";
import { createIcloud } from "./icloud.js";
import { getToken } from "./msal.js";
import { createOutlook } from "./outlook.js";

const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export const createLocalOutlook = () => createOutlook({ getToken });

export const createLocalIcloud = () =>
  createIcloud({
    timeZone,
    getCredentials: async () => {
      const { icloudUser } = readConfig();
      return { user: icloudUser, password: icloudUser && readIcloudPassword(icloudUser) };
    },
  });
