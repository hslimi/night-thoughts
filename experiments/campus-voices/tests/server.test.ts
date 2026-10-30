import type { Server } from "node:http";
import { afterEach, describe, expect, it } from "vitest";
import { createApp } from "../server/app";

let server: Server | undefined;

afterEach(async () => {
  if (!server) return;
  await new Promise<void>((resolve, reject) => {
    server?.close((error) => (error ? reject(error) : resolve()));
  });
  server = undefined;
});

async function startTestServer(): Promise<string> {
  const app = await createApp({
    mode: "test",
    generateFeedback: async () => ({
      message: "A supportive test reflection.",
      source: "scripted",
    }),
  });
  server = app.listen(0, "127.0.0.1");
  await new Promise<void>((resolve) => server?.once("listening", resolve));
  const address = server.address();
  if (!address || typeof address === "string")
    throw new Error("Test server has no TCP address.");
  return `http://127.0.0.1:${address.port}`;
}

describe("application server", () => {
  it("reports only non-sensitive provider and privacy status", async () => {
    const baseUrl = await startTestServer();
    const response = await fetch(`${baseUrl}/api/health`);
    const body = await response.json();
    expect(response.status).toBe(200);
    expect(body).toEqual({
      status: "ok",
      voiceProvider: "scripted",
      dessa: "disabled",
      recordings: false,
      transcripts: false,
    });
    expect(JSON.stringify(body)).not.toContain("apiKey");
  });

  it("returns supportive feedback for valid anonymous metrics", async () => {
    const baseUrl = await startTestServer();
    const response = await fetch(`${baseUrl}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        preConfidence: 3,
        completedGoalIds: ["opening"],
        elapsedSeconds: 60,
      }),
    });
    expect(response.status).toBe(200);
    expect((await response.json()).message).toContain("supportive");
  });

  it("rejects unexpected or out-of-range practice data", async () => {
    const baseUrl = await startTestServer();
    const response = await fetch(`${baseUrl}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        preConfidence: 10,
        completedGoalIds: [],
        elapsedSeconds: 60,
      }),
    });
    expect(response.status).toBe(400);
  });
});
