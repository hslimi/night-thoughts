import path from "node:path";
import { fileURLToPath } from "node:url";
import express, { type Express } from "express";
import {
  createFeedbackGenerator,
  parseFeedbackInput,
  type FeedbackGenerator,
} from "./feedback.js";

interface AppOptions {
  mode: "development" | "production" | "test";
  generateFeedback?: FeedbackGenerator;
}

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDirectory, "..");

export async function createApp(options: AppOptions): Promise<Express> {
  const app = express();
  const generateFeedback =
    options.generateFeedback ??
    createFeedbackGenerator({
      baseUrl: process.env.OMLX_BASE_URL,
      model: process.env.OMLX_MODEL,
      apiKey: process.env.OMLX_API_KEY,
    });

  app.disable("x-powered-by");
  app.use(express.json({ limit: "4kb" }));
  app.use((_request, response, next) => {
    response.setHeader("X-Content-Type-Options", "nosniff");
    response.setHeader("Referrer-Policy", "no-referrer");
    response.setHeader("X-Frame-Options", "DENY");
    response.setHeader(
      "Permissions-Policy",
      "microphone=(self), camera=(), geolocation=()",
    );
    if (options.mode === "production") {
      response.setHeader(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; media-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
      );
    }
    next();
  });

  app.get("/api/health", (_request, response) => {
    response.json({
      status: "ok",
      voiceProvider: "scripted",
      dessa: "disabled",
      recordings: false,
      transcripts: false,
    });
  });

  app.post("/api/feedback", async (request, response) => {
    const input = parseFeedbackInput(request.body);
    if (!input) {
      response
        .status(400)
        .json({ error: "Invalid anonymous practice metrics." });
      return;
    }
    const feedback = await generateFeedback(input);
    response.json(feedback);
  });

  if (options.mode === "development") {
    const { createServer } = await import("vite");
    const vite = await createServer({
      root: path.join(projectRoot, "app"),
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else if (options.mode === "production") {
    const distDirectory = path.join(projectRoot, "dist");
    app.use(express.static(distDirectory));
    app.get(/.*/, (_request, response) => {
      response.sendFile(path.join(distDirectory, "index.html"));
    });
  }

  return app;
}
