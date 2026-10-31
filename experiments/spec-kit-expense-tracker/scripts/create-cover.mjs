import sharp from '../../../../node_modules/sharp/dist/index.cjs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const width = 1600;
const height = 840;
const svg = `
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="1600" height="840" fill="#102f27"/>
  <rect x="0" y="0" width="18" height="840" fill="#41a37b"/>
  <circle cx="1490" cy="-40" r="310" fill="none" stroke="#2d6653" stroke-width="70"/>
  <text x="64" y="90" fill="#a9d9c4" font-family="Arial, sans-serif" font-size="22" font-weight="700" letter-spacing="2">NIGHT THOUGHTS / REPRODUCIBLE EXPERIMENT</text>
  <text x="64" y="190" fill="#ffffff" font-family="Arial, sans-serif" font-size="62" font-weight="800">BEYOND</text>
  <text x="64" y="262" fill="#ffffff" font-family="Arial, sans-serif" font-size="62" font-weight="800">VIBE CODING</text>
  <text x="64" y="320" fill="#d6eee3" font-family="Arial, sans-serif" font-size="28">Build and maintain an expense tracker</text>
  <text x="64" y="358" fill="#d6eee3" font-family="Arial, sans-serif" font-size="28">with GitHub Spec Kit</text>
  <g font-family="Arial, sans-serif" font-size="22" font-weight="700">
    <rect x="64" y="440" width="210" height="58" rx="12" fill="#1d4d3e"/><text x="86" y="477" fill="#ffffff">01 SPECIFY</text>
    <rect x="64" y="516" width="210" height="58" rx="12" fill="#1d4d3e"/><text x="86" y="553" fill="#ffffff">02 CLARIFY</text>
    <rect x="64" y="592" width="210" height="58" rx="12" fill="#1d4d3e"/><text x="86" y="629" fill="#ffffff">03 PLAN</text>
    <rect x="64" y="668" width="210" height="58" rx="12" fill="#1d4d3e"/><text x="86" y="705" fill="#ffffff">04 VERIFY</text>
  </g>
  <path d="M302 469 L355 469 M355 545 L355 469 M355 545 L355 621 M355 621 L355 697" stroke="#76c39f" stroke-width="5" fill="none"/>
  <text x="390" y="484" fill="#a9d9c4" font-family="Arial, sans-serif" font-size="24">Intent</text>
  <text x="390" y="560" fill="#a9d9c4" font-family="Arial, sans-serif" font-size="24">Decisions</text>
  <text x="390" y="636" fill="#a9d9c4" font-family="Arial, sans-serif" font-size="24">Tasks</text>
  <text x="390" y="712" fill="#a9d9c4" font-family="Arial, sans-serif" font-size="24">Evidence</text>
  <rect x="756" y="154" width="800" height="540" rx="24" fill="#ffffff" opacity="0.12"/>
  <text x="790" y="748" fill="#a9d9c4" font-family="Arial, sans-serif" font-size="22">REACT · TYPESCRIPT · INTEGER CENTS · REAL BROWSER TESTS</text>
</svg>`;

const dashboard = await sharp(path.join(root, 'assets', 'screenshots', '10-desktop-dashboard.png'))
  .resize(770, 481, { fit: 'cover' })
  .png()
  .toBuffer();

await sharp(Buffer.from(svg))
  .composite([{ input: dashboard, left: 770, top: 180 }])
  .png({ compressionLevel: 9 })
  .toFile(path.join(root, 'article', 'assets', 'cover.png'));
console.log('Created article/assets/cover.png from the actual dashboard and experiment workflow.');
