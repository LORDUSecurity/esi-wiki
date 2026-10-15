"""Mirror-to-text pipeline for the EsiHub corpus, and the search it feeds.

The wiki's own catalogue only holds files for S1-S2; esihub.net points at hundreds of public
Drive folders covering S1-S5. `tools/esihub_fetch.py` downloads them, this module turns them
into searchable text, and the assistant can then quote a real polycopié instead of guessing.

Two roots are indexed, because a student's question does not care where the PDF came from: the
`corpus/` mirror (every semester, S1-S5) and the repo's own `courses/` files, which `seed_catalog`
already catalogued for S1-S2 but nothing could read until they went through here. The mirror
rows are keyed by their Drive id; the repo rows by `depot-<resource pk>`.

Everything is local: SQLite FTS5 with accent folding, no embedding model, no API key. With
`corpus/` absent — as in the shared sample build — the mirror contributes nothing and the repo's
own documents are still searchable.
"""

import html
import json
import re
import zipfile
from pathlib import Path

from django.conf import settings
from django.db import connection

from .models import CorpusChunk, CorpusDoc, Resource

CHUNK_CHARS = 1400
TEXT_SUFFIXES = {".pdf", ".txt", ".md", ".docx", ".pptx", ".csv"}

# FTS5 keeps its own copy of the text. `remove_diacritics` is what lets "reseau" hit
# "réseau" — the same reason the catalogue search folds accents in Python.
FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
    body,
    chunk_id UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 1'
)
"""

# Words that are in every question about this site and carry no signal.
STOP = {
    "les", "des", "pour", "avec", "dans", "sur", "est", "une", "que", "qui", "quoi",
    "quel", "quelle", "quels", "comment", "cours", "module", "modules", "document",
    "documents", "fichier", "fichiers", "page", "pages", "chapitre", "the", "and",
    "plus", "tres", "bien", "moi", "vous", "nous", "est", "mon", "ma", "mes",
    # Talk words. They sit in a question about anything, they appear inside any document, and
    # two of them ("Quelques conseils") were enough to quote a student CV as course material.
    "quelques", "conseil", "conseils", "suggestion", "suggestions", "exemple", "exemples",
    "chose", "choses", "partie", "maniere", "facon", "genre", "question", "quest",
    # Verbs that open a request. They are how a student asks, not what the course is about, and
    # keeping them cost real answers: « Explique DHCP » demanded a passage covering both
    # "explique" and "DHCP", found none, and the assistant said the documents said nothing
    # about DHCP when 64 of them do.
    "explique", "expliquer", "expliques", "definis", "definir", "definition", "resume",
    "resumer", "donne", "donner", "montre", "montrer", "cite", "citer", "peux", "pourrais",
    "decris", "decrire", "presente", "presenter",
    "reponse", "bonjour", "merci", "svp", "peut", "veux", "veut", "fais", "faire",
    "parle", "parler", "raconte", "connais", "connaitre",
}


def corpus_root():
    return Path(settings.CORPUS_DIR)


def available():
    return corpus_root().exists()


def _pdf_text(path):
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            return "", 0
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages), len(reader.pages)


def _ooxml_text(path):
    """docx and pptx are zip archives of XML; only the runs matter."""
    parts, slides = [], 0
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if re.match(r"(word/document\.xml|ppt/slides/slide\d+\.xml)$", n)]
        for name in sorted(names):
            xml = zf.read(name).decode("utf-8", "replace")
            xml = re.sub(r"</w:p>|</a:p>", "\n", xml)
            parts.append(re.sub(r"<[^>]+>", "", xml))
            slides += 1
    return "\n".join(parts), slides


def extract_text(path):
    path = Path(path)
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            return _pdf_text(path)
        if ext in (".docx", ".pptx"):
            return _ooxml_text(path)
        if ext in (".txt", ".md", ".csv"):
            return path.read_text(encoding="utf-8", errors="replace"), 1
    except Exception:
        return "", 0
    return "", 0


def _clean(text):
    # pypdf and docx XML hand back unpaired surrogates (a split emoji) now and then;
    # SQLite encodes its parameters as UTF-8 and raises UnicodeEncodeError on those.
    text = text.encode("utf-8", "ignore").decode("utf-8")
    # Private-use bullets (Wingdings/Symbol escapes such as \uf0a2) survive extraction and
    # show up inside a quoted passage as tofu boxes.
    text = re.sub(r"[\ue000-\uf8ff]", " ", text)
    text = re.sub(r"\x00", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunked(text, size=CHUNK_CHARS):
    """Paragraph-sized slices: splitting mid-sentence is how a definition loses its subject."""
    chunks, buf = [], ""
    for para in (p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()):
        while len(para) > size:
            cut = para.rfind(" ", 0, size) or size
            chunks.append(para[:cut].strip())
            para = para[cut:].strip()
        if len(buf) + len(para) + 2 > size:
            if buf:
                chunks.append(buf)
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        chunks.append(buf)
    return chunks


def manifest_records():
    """Every file the fetcher pulled, from corpus/manifest.jsonl."""
    path = corpus_root() / "manifest.jsonl"
    if not path.exists():
        return
    seen = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not rec.get("ok") or rec["path"] in seen:
            continue
        seen.add(rec["path"])
        yield rec


def depot_records():
    """The repo's own `courses/` files, as index records shaped like the manifest's.

    The folder layout says nothing useful about these PDFs, so the labels come from the rows
    `seed_catalog` already built: semester, unit code and kind are curated there, and keying by
    the resource id keeps a re-index from ever colliding with a Drive id.

    Files the mirror already contributed are skipped: EsiHub carries most of S1-S2 too, and the
    same text indexed twice dilutes `document_frequency` and shows the student one document as
    two sources. Name and byte size together identify a copy — a name alone does not, since
    `Resume.pdf` and `ESI AO crs 1.pdf` appear in several modules with different content.
    """
    already = {
        (_fold(d.name), d.bytes)
        for d in CorpusDoc.objects.exclude(drive_id__startswith="depot-")
    }
    root = Path(settings.MEDIA_ROOT)
    for r in Resource.objects.filter(origin="depot").select_related("module__semester"):
        full = root / r.path
        if not full.is_file():
            continue
        size = full.stat().st_size
        if (_fold(full.name), size) in already:
            continue
        yield {
            "file_id": f"depot-{r.pk}",
            "path": r.path,
            "root": str(root),
            "name": full.name,
            "semester": r.module.semester.code,
            "branch": r.module.branch,
            "code": r.module.code,
            "kind": r.kind,
            "bytes": size,
        }


def index_record(rec, rebuild=False):
    """(re)index one file from either root. Returns the number of chunks kept."""
    full = Path(rec.get("root") or corpus_root()) / rec["path"]
    if full.suffix.lower() not in TEXT_SUFFIXES or not full.exists():
        return 0
    text, pages = extract_text(full)
    text = _clean(text)
    doc, _ = CorpusDoc.objects.update_or_create(
        drive_id=rec["file_id"],
        defaults={
            "path": rec["path"],
            "name": rec.get("name") or full.name,
            "semester": rec.get("semester", ""),
            "branch": rec.get("branch", ""),
            "module_code": rec.get("code", ""),
            "kind": rec.get("kind", ""),
            "bytes": rec.get("bytes") or full.stat().st_size,
            "pages": pages,
            "chars": len(text),
        },
    )
    cur = connection.cursor()
    cur.execute("DELETE FROM corpus_fts WHERE chunk_id IN (SELECT id FROM catalog_corpuschunk WHERE document_id = %s)", [doc.id])
    doc.chunks.all().delete()
    kept = 0
    for seq, piece in enumerate(chunked(text)):
        if len(piece) < 60:
            continue
        chunk = CorpusChunk.objects.create(document=doc, seq=seq, text=piece)
        cur.execute("INSERT INTO corpus_fts (body, chunk_id) VALUES (%s, %s)", [piece, chunk.id])
        kept += 1
    return kept


def sync_index(limit=None, rebuild=False, verbose=True):
    # The mirror first: it is the bigger set, and `limit` is for trying a few new files.
    records = list(depot_records())
    if available():
        records = list(manifest_records()) + records
    if not records:
        return {"documents": 0, "chunks": 0, "note": "no corpus folder and no catalogued courses"}
    connection.cursor().execute(FTS_DDL)
    if rebuild:
        connection.cursor().execute("DELETE FROM corpus_fts")
        CorpusChunk.objects.all().delete()
        CorpusDoc.objects.all().delete()

    # Anything already recorded is skipped, empty text included: rescanning a scanned exam
    # costs the same as indexing it. Use --rebuild after a fetch, or to pick up new files.
    done = set() if rebuild else set(CorpusDoc.objects.values_list("drive_id", flat=True))
    total = {"documents": 0, "chunks": 0, "empty": 0}
    for rec in records:
        if rec["file_id"] in done or Path(rec["path"]).suffix.lower() not in TEXT_SUFFIXES:
            continue
        kept = index_record(rec)
        if kept:
            total["documents"] += 1
            total["chunks"] += kept
            if verbose:
                print(f"  {rec['path']}: {kept} chunks")
        else:
            total["empty"] += 1
            if verbose:
                print(f"  {rec['path']}: no extractable text (scanned image?)")
        if limit and total["documents"] >= limit:
            break
    return total


def query_terms(question):
    folded = re.sub(r"[^\w\s]", " ", question)
    return [t for t in re.findall(r"\w{3,}", folded) if t.lower() not in STOP][:12]


def _fold(text):
    import unicodedata

    return "".join(
        c for c in unicodedata.normalize("NFKD", str(text).lower()) if not unicodedata.combining(c)
    )


def _covered(terms, text):
    hay = _fold(text)
    out = []
    for t in terms:
        f = re.escape(_fold(t))
        # A short term has to be the whole word: prefix matching is what let "CAP" be answered
        # from a page about "capacité". Long terms keep the prefix, which is how "reseau" finds
        # "Réseaux" and "revolution" finds "révolutions" once accents are folded away.
        if re.search(rf"\b{f}\b" if len(f) < 5 else rf"\b{f}", hay):
            out.append(t)
    return out


def document_frequency(term, total):
    """Chunks a term appears in — how rare it is in this corpus, measured not assumed."""
    with connection.cursor() as cur:
        try:
            cur.execute("SELECT count(*) FROM corpus_fts WHERE corpus_fts MATCH %s", [f'"{term}"*'])
            n = cur.fetchone()[0]
        except Exception:
            return total
    return n


def search(question, hits=5):
    """BM25 over every indexed document, mirror or repo: [{'text','doc','score'}], best first.

    FTS5 MATCH is an OR over the question's words, and bm25 always returns something: with no
    relevant polycopié it hands back the least irrelevant paragraphs. Those would answer as
    fact, so a hit only counts when it covers two question words and at least one word rare
    enough to identify the subject. Nothing passing means an empty list, and the models speak.
    """
    terms = query_terms(question)
    if not terms:
        return []
    match = " OR ".join(f'"{t}"*' for t in terms)
    with connection.cursor() as cur:
        try:
            cur.execute(
                "SELECT chunk_id, bm25(corpus_fts) FROM corpus_fts "
                "WHERE corpus_fts MATCH %s ORDER BY bm25(corpus_fts) LIMIT %s",
                [match, hits],
            )
            rows = cur.fetchall()
            cur.execute("SELECT count(*) FROM corpus_fts")
            total = max(cur.fetchone()[0], 1)
        except Exception:
            # No index yet — a database that never ran `index_corpus` has no such table at all.
            return []
    if not rows:
        return []
    frequencies = {t: document_frequency(t, total) for t in terms}
    rare = {t for t, df in frequencies.items() if df <= max(2, round(0.12 * total))}
    # The rarest word of the question is its subject. A passage that skips it is a document
    # that happens to share two other words — which is how an OSPF question quoted the
    # host-network layer of the same course.
    rarest = min(frequencies, key=frequencies.get)
    by_id = {
        c.id: c
        for c in CorpusChunk.objects.select_related("document").filter(pk__in=[r[0] for r in rows])
    }
    kept = []
    seen = set()
    for i, s in rows:
        chunk = by_id.get(i)
        if chunk is None:
            continue
        covered = _covered(terms, chunk.text)
        if rarest not in covered:
            continue
        if len(covered) >= min(2, len(terms)) and (not rare or rare.intersection(covered)):
            # One PDF can sit in two filière folders, so it indexes as two documents. The student
            # is reading one file, and "Hive — ICSD" plus "Hive — IIN" reads like two sources.
            name = _fold(chunk.document.name)
            if name in seen:
                continue
            seen.add(name)
            kept.append({"text": chunk.text, "doc": chunk.document, "score": s})
    return kept


def cite(hit):
    doc = hit["doc"]
    # Some EsiHub folders are literally named "module", which is not a code worth printing.
    code = doc.module_code if doc.module_code.lower() != "module" else ""
    # Names scraped off the Drive folder pages arrived entity-escaped ("d&#39;anxiété.pdf") and
    # stay that way on disk, so the citation is where they become readable again.
    return " — ".join(
        part
        for part in (
            html.unescape(doc.name),
            " ".join(x for x in (doc.branch, doc.semester, f"module {code}" if code else "") if x),
            doc.kind,
        )
        if part
    )


def clip(text, limit=900):
    """Quote at most `limit` characters, ending on a line break. The verbatim fallback is read
    as course material, and a passage cut at "PROTOCOLE IPV" reads as a broken page."""
    if len(text) <= limit:
        return text
    cut = text.rfind("\n", 0, limit)
    if cut < limit // 2:
        cut = text.rfind(" ", 0, limit)
    return (text[: cut if cut > 0 else limit].rstrip() + " …")


def best_documents(hits, keep=2):
    """One passage per document: two chunks of the same polycopié is one source, said twice."""
    picked, seen = [], set()
    for hit in hits:
        if hit["doc"].id in seen:
            continue
        seen.add(hit["doc"].id)
        picked.append(hit)
        if len(picked) >= keep:
            break
    return picked
