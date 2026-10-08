// Offline smoke test: starts the MCP server and checks that all tools are registered.
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const client = new Client({ name: "smoke", version: "1.0.0" });
await client.connect(new StdioClientTransport({ command: "node", args: ["src/index.js"] }));
const { tools } = await client.listTools();
console.log(tools.map((t) => t.name).join("\n"));
if (tools.length !== 15) throw new Error(`expected 15 tools, got ${tools.length}`);
const res = await client.callTool({ name: "calendar_list_calendars", arguments: {} });
console.log("not configured ->", res.isError, res.content[0].text);
await client.close();
