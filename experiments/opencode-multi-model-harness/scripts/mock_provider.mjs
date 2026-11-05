#!/usr/bin/env node
// Local OpenAI-compatible provider that fails on purpose, for failover tests.
//
// Model IDs choose the failure:
//   mock-429-after-tool  First call writes notes.txt with a tool call. Later calls return 429.
//   mock-503             Always returns 503.
//   mock-stall           Accepts the request and never sends a first token.
//
// Every request is logged to stdout as one JSON line. Bound to 127.0.0.1.
// Usage: node mock_provider.mjs [port]     Stop with: curl -X POST 127.0.0.1:<port>/shutdown
import { createServer } from "node:http";

const port = Number(process.argv[2] ?? 8899);
const calls = new Map();

function toolName(tools, wanted) {
  return (tools ?? []).map((t) => t.function?.name).find((name) => name === wanted);
}

function sse(res, chunks) {
  res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" });
  for (const chunk of chunks) res.write(`data: ${JSON.stringify(chunk)}\n\n`);
  res.write("data: [DONE]\n\n");
  res.end();
}

function writeToolCall(model, path, content) {
  const base = { id: "mock-1", object: "chat.completion.chunk", created: 0, model };
  return [
    {
      ...base,
      choices: [{
        index: 0,
        delta: {
          role: "assistant",
          tool_calls: [{ index: 0, id: "call_mock_1", type: "function", function: { name: "write", arguments: JSON.stringify({ filePath: path, path, content }) } }],
        },
        finish_reason: null,
      }],
    },
    { ...base, choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }], usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } },
  ];
}

const server = createServer((req, res) => {
  let body = "";
  req.on("data", (d) => (body += d));
  req.on("end", () => {
    if (req.url === "/shutdown") {
      res.end("bye\n");
      server.close();
      setTimeout(() => process.exit(0), 50);
      return;
    }
    if (req.method !== "POST" || !req.url.endsWith("/chat/completions")) {
      res.writeHead(404).end();
      return;
    }
    const request = JSON.parse(body);
    const model = request.model;
    const count = (calls.get(model) ?? 0) + 1;
    calls.set(model, count);
    const hasWrite = Boolean(toolName(request.tools, "write"));
    console.log(JSON.stringify({ at: new Date().toISOString(), model, call: count, messages: request.messages?.length, hasWrite }));

    if (model === "mock-503") {
      res.writeHead(503, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: { message: "mock: service unavailable", type: "overloaded", code: 503 } }));
    } else if (model === "mock-stall") {
      req.socket.setTimeout(0); // Hold the connection open and send nothing.
    } else if (model === "mock-429-after-tool" && count === 1 && hasWrite) {
      sse(res, writeToolCall(model, "notes.txt", "written once by the mock provider\n"));
    } else {
      res.writeHead(429, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: { message: "mock: rate limit exceeded", type: "rate_limit_error", code: 429 } }));
    }
  });
});

server.listen(port, "127.0.0.1", () => console.log(JSON.stringify({ listening: port })));
