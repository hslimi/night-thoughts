import sharp from '../../../../node_modules/sharp/dist/index.cjs';
import { readdir, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const input = path.join(root, 'assets', 'screenshots');
const output = path.join(root, 'article', 'assets');
await mkdir(output, { recursive: true });

for (const filename of (await readdir(input)).filter((name) => name.endsWith('.png')).sort()) {
  await sharp(path.join(input, filename))
    .resize({ width: 1600, withoutEnlargement: true })
    .png({ compressionLevel: 9 })
    .toFile(path.join(output, filename));
  console.log(`Prepared article/assets/${filename}`);
}
