// Crawl esihub.net branch pages into tools/esihub-catalog.json.
// The site is static Hugo HTML: each branch page holds every course of every
// semester with Course/Exam/Summary links to Google Drive folders.
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const BRANCHES = ['icsd', 'idc', 'iin', 'issic', 'isitd', 'msics'];
const KINDS = { Course: 'cours', Exam: 'examen', Summary: 'resume' };
const OUT = fileURLToPath(new URL('./esihub-catalog.json', import.meta.url));

async function get(url) {
  const res = await fetch(url, { headers: { 'User-Agent': 'ESI-Wiki/1.0 (projet etudiant)' } });
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return res.text();
}

// <div id=semester-1-year-2022 class="year-content ..."> opens a block that runs
// until the next such div, so split on the marker and keep its attributes.
function parseBranch(html, branch) {
  const chunks = html.split(/(?=<div id=semester-\d+-year-)/).slice(1);
  const docs = [];
  for (const chunk of chunks) {
    const head = chunk.slice(0, 400);
    const semester = /data-semester=(\d+)/.exec(head)?.[1];
    const year = /data-year=([^ >]+|"[^"]+")/.exec(head)?.[1]?.replace(/"/g, '');
    if (!semester) continue;
    const cards = chunk.split(/(?=<h4[^>]*>)/);
    for (const card of cards.slice(1)) {
      const title = /<h4[^>]*>([^<]+)<\/h4>/.exec(card)?.[1];
      if (!title) continue;
      const links = {};
      const re = /color:#6b7280>([A-Za-z]+):<\/span>\s*<a href=(?:"([^"]+)"|'([^']+)'|([^\s>]+))/g;
      for (const m of card.matchAll(re)) {
        const kind = KINDS[m[1]];
        const url = m[2] || m[3] || m[4];
        if (kind && url && !links[kind]) links[kind] = url.trim();
      }
      if (!Object.keys(links).length) continue;
      docs.push({
        branch,
        // The site numbers its tabs from 0 in the markup but labels them S1..S5.
        semester: `S${Number(semester) + 1}`,
        year,
        code: /^((?:M\.)?\d+(?:\.\d+)?)/.exec(title)?.[1] || '',
        title: decodeEntities(title.trim()),
        links,
      });
    }
  }
  return docs;
}

const decodeEntities = (s) =>
  s.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(n))
   .replace(/&amp;/g, '&')
   .replace(/&#39;/g, "'")
   .replace(/&quot;/g, '"');

const all = [];
for (const branch of BRANCHES) {
  const url = `https://esihub.net/docs-esi-/${branch}/`;
  try {
    const docs = parseBranch(await get(url), branch.toUpperCase());
    all.push(...docs);
    console.log(`${branch.padEnd(9)} ${String(docs.length).padStart(3)} courses`);
  } catch (err) {
    console.warn(`${branch.padEnd(9)} skipped: ${err.message}`);
  }
}

// The site's search index already holds the PFE reports with their metadata,
// so there is no need to scrape the 46 report pages.
function parseReports(index) {
  return index
    .filter((e) => e.isReport)
    .map((e) => ({
      title: (e.title || '').trim(),
      engineer: e.engineer || '',
      organisation: e.organisation || '',
      promotion: String(e.promotion || ''),
      language: e.language || '',
      tags: e.tags || [],
      abstract: (e.content || '').replace(/^Abstract\s*#\s*/i, '').trim(),
      reportUrl: e.reportLink || '',
      presentationUrl: e.presentationLink || '',
      page: e.permalink ? `${e.permalink.replace(/\/+$/, '')}/` : '',
    }));
}

let reports = [];
try {
  reports = parseReports(JSON.parse(await get('https://esihub.net/index.json')));
  console.log(`reports   ${String(reports.length).padStart(3)} PFE reports`);
} catch (err) {
  console.warn(`reports   skipped: ${err.message}`);
}

const linkCount = all.reduce((n, d) => n + Object.keys(d.links).length, 0);
const payload = {
  meta: { source: 'esihub.net', crawled: new Date().toISOString() },
  courses: all,
  reports,
};
await writeFile(OUT, JSON.stringify(payload, null, 1), 'utf8');
console.log(`\n${all.length} courses (${linkCount} drive links), ${reports.length} reports -> tools/esihub-catalog.json`);
