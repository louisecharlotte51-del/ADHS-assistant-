#!/usr/bin/env node
// Local version for Claude Desktop on the Mac (stdio).
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createLocalIcloud, createLocalOutlook } from "./local.js";
import { registerTools } from "./tools.js";

const server = new McpServer({ name: "adhs-assistant", version: "1.0.0" });
const outlook = createLocalOutlook();
const icloud = createLocalIcloud();
registerTools(server, { outlook: () => outlook, icloud: () => icloud });

await server.connect(new StdioServerTransport());
