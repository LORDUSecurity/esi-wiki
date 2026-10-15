#!/usr/bin/env node
// Two-phase media pipeline against Wikimedia Commons (CC / public-domain, attribution captured).
//   node tools/fetch-media.mjs preview   -> writes tools/candidates.json + small preview thumbs
//   node tools/fetch-media.mjs fetch     -> downloads full-res for entries marked picked in candidates.json
import { writeFile, mkdir, readFile } from 'node:fs/promises';
import { join, basename } from 'node:path';

const API = 'https://commons.wikimedia.org/w/api.php';
const UA = 'ESI-Wiki-site-builder/1.0 (educational site rebuild; https://github.com/LORDUSecurity/esi-wiki)';
const OUT = 'frontend/public/media';
const CAND = 'tools/candidates.json';
const FULL_WIDTH = 2560;

const Q = 'incategory:"Quality images"';
const TOPICS = [
  { key: 'hero', queries: [`${Q} university campus`, `${Q} modern university building`, `${Q} campus aerial`], per: 8 },
  { key: 'campus', queries: [`${Q} university building`, `${Q} faculty architecture`], per: 6 },
  { key: 'library', queries: [`${Q} university library`, `${Q} library reading room interior`], per: 6 },
  { key: 'lecture', queries: [`${Q} lecture hall`, `${Q} amphitheatre university`, `${Q} auditorium interior`], per: 6 },
  { key: 'students', queries: [`${Q} students studying`, `${Q} university students classroom`], per: 6 },
  { key: 'lab', queries: [`${Q} computer laboratory`, `${Q} computer science students`, `${Q} servers datacenter`], per: 6 },
  { key: 'graduation', queries: [`${Q} graduation ceremony`, `${Q} graduation mortarboard`], per: 6 },
  { key: 'life', queries: [`${Q} campus students outdoors`, `${Q} university student life`, `${Q} library desk`], per: 6 },
  { key: 'rabat', queries: [`${Q} Rabat Morocco`, `${Q} Hassan Tower Rabat`, `${Q} Morocco modern architecture`], per: 6 },
  { key: 'video', queries: ['filetype:video university', 'filetype:video campus timelapse', 'filetype:video students classroom'], per: 6, video: true },
];

async function api(params) {
  const url = new URL(API);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { 'User-Agent': UA } });
  if (!res.ok) throw new Error(`Commons ${res.status}`);
  return res.json();
}

const clean = (v) => (v?.value ?? '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();

async function searchOne(topic, query, width) {
  const s = await api({
    action: 'query', format: 'json', list: 'search', srsearch: query,
    srnamespace: '6', srlimit: String(topic.per * 3),
  });
  const titles = (s?.query?.search ?? []).map((h) => h.title);
  if (!titles.length) return [];
  const out = [];
  for (const chunk of Object.values(group(titles, 25))) {
    const info = await api({
      action: 'query', format: 'json', titles: chunk.join('|'),
      prop: 'imageinfo', iiprop: 'url|size|mime|extmetadata', iiurlwidth: String(width),
    });
    for (const p of Object.values(info?.query?.pages ?? {})) {
      const i = p.imageinfo?.[0];
      if (!i) continue;
      const isVideo = i.mime.startsWith('video');
      if (Boolean(topic.video) !== isVideo) continue;
      const meta = i.extmetadata ?? {};
      out.push({
        title: p.title,
        page: i.descriptionurl,
        url: isVideo ? i.url : (i.thumburl || i.url),
        full: i.url,
        bytes: i.size,
        mime: i.mime,
        width: i.width,
        height: i.height,
        artist: clean(meta.Artist) || 'Wikimedia contributor',
        license: clean(meta.LicenseShortName) || 'CC',
        licenseUrl: clean(meta.LicenseUrl),
      });
    }
  }
  return out;
}

const group = (arr, n) => {
  const out = [];
  for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n));
  return out;
};

async function preview() {
  const all = {};
  for (const topic of TOPICS) {
    const seen = new Set();
    const items = [];
    for (const query of topic.queries) {
      let found = [];
      try {
        found = await searchOne(topic, query, topic.video ? 960 : 640);
      } catch (e) {
        console.warn(`[${topic.key}] ${e.message}`);
        continue;
      }
      for (const it of found) {
        if (seen.has(it.title)) continue;
        if (!topic.video && it.width < 1400) continue;
        if (topic.video && it.bytes > 30_000_000) continue;
        seen.add(it.title);
        items.push({ ...it, topic: topic.key, picked: false });
        if (items.length >= topic.per) break;
      }
      if (items.length >= topic.per) break;
    }
    all[topic.key] = items;
    console.log(`[${topic.key}] ${items.length} candidates`);
  }
  await mkdir('tools/preview', { recursive: true });
  for (const items of Object.values(all)) {
    for (const it of items) {
      if (it.mime.startsWith('video')) continue;
      const dest = join('tools/preview', `${hash(it.title)}.jpg`);
      it.preview = `/tools/preview/${basename(dest)}`;
      try {
        const res = await fetch(it.url, { headers: { 'User-Agent': UA } });
        if (res.ok) await writeFile(dest, Buffer.from(await res.arrayBuffer()));
      } catch (e) {
        console.warn(`preview ${it.title}: ${e.message}`);
      }
    }
  }
  await writeFile(CAND, JSON.stringify(all, null, 2));
  console.log(`\nWrote ${CAND}. Run the sheet builder to review.`);
}

const hash = (s) => {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  return h.toString(36);
};

async function fetchPicked() {
  const all = JSON.parse(await readFile(CAND, 'utf8'));
  const manifest = [];
  for (const [topicKey, items] of Object.entries(all)) {
    const chosen = items.filter((i) => i.picked);
    if (!chosen.length) {
      console.warn(`[${topicKey}] none picked`);
      continue;
    }
    const dir = join(OUT, topicKey);
    await mkdir(dir, { recursive: true });
    for (let n = 0; n < chosen.length; n++) {
      const it = chosen[n];
      const src = it.mime.startsWith('video') ? it.full : await fullUrl(it, topicKey === 'hero' ? 2560 : 1800);
      const name = basename(src.split('?')[0]).replace(/[^A-Za-z0-9._-]/g, '_');
      const dest = join(dir, `${String(n + 1).padStart(2, '0')}-${name}`);
      const res = await fetch(src, { headers: { 'User-Agent': UA }, redirect: 'follow' });
      if (!res.ok) {
        console.warn(`[${topicKey}] ${res.status} ${name}`);
        continue;
      }
      const buf = Buffer.from(await res.arrayBuffer());
      if (buf.byteLength < 20_000) {
        console.warn(`[${topicKey}] too small ${name}`);
        continue;
      }
      await writeFile(dest, buf);
      manifest.push({ ...it, bytes: buf.byteLength, file: `/media/${topicKey}/${basename(dest)}`, url: src });
      console.log(`[${topicKey}] ${basename(dest)} (${(buf.byteLength / 1048576).toFixed(1)} MB)`);
    }
  }
  await mkdir('frontend/src/data', { recursive: true });
  await writeFile('frontend/src/data/media.json', JSON.stringify(manifest, null, 2));
  console.log(`\n${manifest.length} assets -> frontend/src/data/media.json`);
}

// Re-request the large rendition at full width for stills we only saw as previews.
async function fullUrl(it, width = FULL_WIDTH) {
  const j = await api({
    action: 'query', format: 'json', titles: it.title,
    prop: 'imageinfo', iiprop: 'url', iiurlwidth: String(width),
  });
  const p = Object.values(j?.query?.pages ?? {})[0];
  return p?.imageinfo?.[0]?.thumburl || p?.imageinfo?.[0]?.url || it.url;
}

const mode = process.argv[2];
if (mode === 'preview') await preview();
else if (mode === 'fetch') await fetchPicked();
else console.log('usage: node tools/fetch-media.mjs [preview|fetch]');
