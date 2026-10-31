import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = await readFile(path.join(root, 'article', 'article.md'), 'utf8');
const uploads = await readFile(path.join(root, 'evidence', 'hashnode-images.txt'), 'utf8');
const mapping = new Map();
for (const line of uploads.split('\n')) {
  const match = line.match(/^(article\/assets\/(\S+\.png))\s+(https:\/\/cdn\.hashnode\.com\/\S+\.png)$/);
  if (match) mapping.set(`assets/${match[2]}`, match[3]);
}
let content = source;
for (const [local, cdn] of mapping) {
  content = content.replaceAll(`](${local})`, `](${cdn})`);
}
const imageRefs = [...content.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)].map((match) => match[1]);
if (imageRefs.length !== 16 || imageRefs.some((ref) => !ref.startsWith('https://cdn.hashnode.com/'))) {
  throw new Error('Not every inline image has a Hashnode CDN URL');
}
if (/localhost|127\.0\.0\.1|\/Users\/|\]\(assets\//.test(content)) {
  throw new Error('Local path or localhost content remains in Hashnode Markdown');
}
await writeFile(path.join(root, 'article', 'hashnode.md'), content);
await writeFile(path.join(root, 'evidence', 'hashnode-cover-url.txt'), `${mapping.get('assets/cover.png')}\n`);
console.log(`Prepared article/hashnode.md with ${imageRefs.length} CDN inline images.`);
