import { chromium } from "@playwright/test";
import { readFile } from "node:fs/promises";

const dashboard = await readFile("evidence/.capture-tmp/10-desktop-dashboard.png");
const image = `data:image/png;base64,${dashboard.toString("base64")}`;
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  await page.setContent(`<!doctype html>
    <html><head><meta charset="utf-8"><style>
      * { box-sizing: border-box; }
      body { margin: 0; width: 1600px; height: 900px; overflow: hidden; background: #102b26; color: #f7fbf8; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      main { height: 100%; padding: 72px 80px; position: relative; background: radial-gradient(circle at 85% 12%, #285c4c 0, transparent 38%), #102b26; }
      .kicker { color: #8dd7bb; font-size: 20px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
      h1 { max-width: 780px; margin: 24px 0 20px; font-size: 72px; line-height: 1.03; letter-spacing: -.045em; }
      .subtitle { max-width: 700px; margin: 0; color: #c5d9d1; font-size: 27px; line-height: 1.45; }
      .workflow { display: flex; align-items: center; gap: 12px; margin-top: 48px; }
      .step { padding: 13px 17px; border: 1px solid #4f7b6c; border-radius: 10px; color: #eaf6f0; font-size: 17px; font-weight: 650; background: #173c33; }
      .arrow { color: #8dd7bb; font-size: 22px; }
      .shot { position: absolute; right: 70px; bottom: -100px; width: 850px; border: 1px solid #5e8d7c; border-radius: 20px; box-shadow: 0 28px 80px #071a15aa; overflow: hidden; transform: rotate(-2deg); background: white; }
      .shot img { display: block; width: 100%; }
      .label { position: absolute; left: 80px; bottom: 76px; color: #a9c7bb; font-size: 19px; }
    </style></head><body><main>
      <div class="kicker">GitHub Spec Kit · practical experiment</div>
      <h1>Beyond Vibe Coding</h1>
      <p class="subtitle">Building and maintaining an expense tracker with visible specifications, quality gates, convergence, and structured bug fixing.</p>
      <div class="workflow">
        <span class="step">Specify</span><span class="arrow">→</span>
        <span class="step">Plan</span><span class="arrow">→</span>
        <span class="step">Tasks</span><span class="arrow">→</span>
        <span class="step">Build</span><span class="arrow">→</span>
        <span class="step">Converge</span><span class="arrow">→</span>
        <span class="step">Fix</span>
      </div>
      <div class="shot"><img src="${image}" alt=""></div>
      <div class="label">React · TypeScript · Vite · Playwright</div>
    </main></body></html>`);
  await page.screenshot({ path: "article/assets/00-cover.png", fullPage: false });
  console.log("Created cover from the actual final dashboard and experiment workflow.");
} finally {
  await browser.close();
}
