#!/usr/bin/env node
// Montage of the candidate previews, so curation is one image read instead of 50.
import { readFile, writeFile } from 'node:fs/promises';
import sharp from 'sharp';

const COLS = 6;
const TW = 320;
const TH = 200;
const CAP = 34;
const PAD = 8;

const all = JSON.parse(await readFile('tools/candidates.json', 'utf8'));
const cells = [];
for (const [topic, items] of Object.entries(all)) {
  items.forEach((it, i) => {
    if (it.mime.startsWith('video')) return;
    cells.push({ id: `${topic}-${String(i + 1).padStart(2, '0')}`, it });
  });
}

const rows = Math.ceil(cells.length / COLS);
const W = COLS * (TW + PAD) + PAD;
const H = rows * (TH + CAP + PAD) + PAD;
const composites = [];

for (let idx = 0; idx < cells.length; idx++) {
  const { id, it } = cells[idx];
  const col = idx % COLS;
  const row = Math.floor(idx / COLS);
  const x = PAD + col * (TW + PAD);
  const y = PAD + row * (TH + CAP + PAD);
  let buf;
  try {
    buf = await sharp(`.${it.preview}`).resize(TW, TH, { fit: 'cover' }).jpeg({ quality: 72 }).toBuffer();
  } catch {
    continue;
  }
  composites.push({ input: buf, left: x, top: y });
  const label = `<svg width="${TW}" height="${CAP}"><rect width="${TW}" height="${CAP}" fill="#101826"/>
    <text x="4" y="14" fill="#e8b64c" font-size="12" font-family="monospace">${id}</text>
    <text x="4" y="28" fill="#8fa2c4" font-size="10" font-family="monospace">${it.width}x${it.height} ${it.license.slice(0, 22)}</text></svg>`;
  composites.push({ input: Buffer.from(label), left: x, top: y + TH });
}

const sheet = await sharp({
  create: { width: W, height: H, channels: 3, background: '#070c18' },
})
  .composite(composites)
  .jpeg({ quality: 78 })
  .toBuffer();

await writeFile('tools/montage.jpg', sheet);
console.log(`tools/montage.jpg ${W}x${H} — ${cells.length} stills`);
