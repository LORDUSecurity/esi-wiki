#!/usr/bin/env node
// Builds a single review sheet from tools/candidates.json so the picks can be eyeballed at once.
import { readFile, writeFile } from 'node:fs/promises';

const all = JSON.parse(await readFile('tools/candidates.json', 'utf8'));
const tiles = [];
for (const [topic, items] of Object.entries(all)) {
  items.forEach((it, i) => {
    const id = `${topic}-${String(i + 1).padStart(2, '0')}`;
    const media = it.mime.startsWith('video')
      ? `<div class="noview">${id}<br>video ${(it.bytes / 1048576).toFixed(0)} MB<br>${it.mime}</div>`
      : `<img src="${it.preview}" loading="lazy">`;
    tiles.push(`
      <figure data-id="${id}">
        ${media}
        <figcaption><b>${id}</b> ${it.width}x${it.height}<br>
        <span class="lic">${it.license}</span>
        <span class="t">${it.title.replace('File:', '').slice(0, 46)}</span></figcaption>
      </figure>`);
  });
}

await writeFile('tools/preview-sheet.html', `<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
 body{background:#0b1020;color:#dfe6f5;font:13px/1.35 system-ui;margin:0;padding:24px}
 h2{margin:22px 0 8px;font-size:14px;letter-spacing:.14em;text-transform:uppercase;color:#e8b64c}
 .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
 figure{margin:0;background:#121a30;border:1px solid #23324f;border-radius:8px;overflow:hidden}
 img{width:100%;height:150px;object-fit:cover;display:block}
 figcaption{padding:6px 8px;font-size:11px;color:#93a4c4}
 .lic{color:#5fd0a8} .t{display:block;color:#6f80a0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .noview{height:150px;display:flex;align-items:center;justify-content:center;text-align:center;color:#e0777a}
</style></head><body>
${Object.keys(all).map((t) => `<h2>${t} (${all[t].length})</h2><div class="grid">${
  tiles.filter((x) => x.includes(`data-id="${t}-`)).join('')}</div>`).join('')}
</body></html>`);

console.log(`tools/preview-sheet.html — ${tiles.length} tiles`);
