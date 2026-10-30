import { createApp } from "./app.js";

const host = process.env.HOST || "127.0.0.1";
const port = Number.parseInt(process.env.PORT || "3000", 10);
const mode =
  process.env.NODE_ENV === "production" ? "production" : "development";
const app = await createApp({ mode });
const server = app.listen(port, host, () => {
  console.log(`Campus Voices listening on http://${host}:${port}`);
});

function shutdown(): void {
  server.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
