"""Mirror the EsiHub Drive folders onto disk so the assistant has something to read.

Every link is a public Drive folder shared by esihub.net; we enumerate its children from
the folderview HTML and pull the files with the same anonymous download URL a browser uses.
Nothing here needs a token, and nothing is uploaded anywhere.

  python tools/esihub_fetch.py                 # everything (~1.4 GB, resumable)
  python tools/esihub_fetch.py --semester S3   # one semester
  python tools/esihub_fetch.py --limit 40      # smoke run
  python tools/esihub_fetch.py --status
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from esihub_drive import DOWNLOAD_URL, UA, list_folder  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CORPUS = Path(os.getenv("WIKI_CORPUS") or REPO / "corpus")
MANIFEST = CORPUS / "manifest.jsonl"
MAX_BYTES = int(os.getenv("ESIHUB_MAX_FILE_MB") or 30) * 1024 * 1024
SLEEP = float(os.getenv("ESIHUB_SLEEP") or 0.35)
SKIP_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}  # no OCR here; scanned pages stay links


def safe(text, limit=70):
    text = re.sub(r"[^\w. -]+", "_", str(text), flags=re.U).strip(" ._")
    return re.sub(r"_{2,}", "_", text)[:limit]


def walk_folders(semester=None, branch=None):
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    from catalog.models import HubCourse

    seen = {}
    qs = HubCourse.objects.all()
    if semester:
        qs = qs.filter(semester=semester)
    if branch:
        qs = qs.filter(branch=branch)
    for course in qs:
        for kind, url in (course.links or {}).items():
            m = re.search(r"/folders/([A-Za-z0-9_-]{10,})", url or "")
            if not m:
                continue
            key = (m.group(1), kind)
            if key in seen:
                continue
            seen[key] = True
            yield {
                "folder": m.group(1),
                "kind": kind,
                "code": course.code or "module",
                "title": course.title,
                "semester": course.semester,
                "branch": course.branch,
            }


def already():
    done = set()
    if MANIFEST.exists():
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("ok"):
                done.add(rec["file_id"])
    return done


def fetch(limit=None, semester=None, branch=None):
    CORPUS.mkdir(parents=True, exist_ok=True)
    done = already()
    got = skipped = failed = 0
    t0 = time.time()
    log = MANIFEST.open("a", encoding="utf-8")
    for info in walk_folders(semester, branch):
        dest_dir = CORPUS / safe(info["semester"]) / safe(info["branch"]) / safe(info["code"]) / safe(info["kind"])
        try:
            entries = list_folder(info["folder"])
        except Exception as e:
            print(f"  folder {info['folder']} unreadable: {type(e).__name__}")
            failed += 1
            continue
        for name, file_id, kind in entries:
            if kind != "file":
                continue
            ext = Path(name).suffix.lower() or ".pdf"
            if ext in SKIP_EXT or file_id in done:
                skipped += 1
                continue
            dest = dest_dir / safe(name, 90)
            if dest.exists() and dest.stat().st_size > 0:
                skipped += 1
                continue
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                r = urllib.request.urlopen(urllib.request.Request(DOWNLOAD_URL.format(file_id), headers=UA), timeout=120)
                if int(r.headers.get("Content-Length") or 0) > MAX_BYTES:
                    log.write(json.dumps({"file_id": file_id, "ok": False, "reason": "too big"}) + "\n")
                    skipped += 1
                    continue
                tmp = dest.with_suffix(dest.suffix + ".part")
                with tmp.open("wb") as fh:
                    shutil.copyfileobj(r, fh, 262144)
                tmp.replace(dest)
                size = dest.stat().st_size
                log.write(json.dumps({
                    "file_id": file_id, "ok": True, "path": str(dest.relative_to(CORPUS)).replace("\\", "/"),
                    "bytes": size, "semester": info["semester"], "branch": info["branch"],
                    "code": info["code"], "kind": info["kind"], "name": name,
                }) + "\n")
                log.flush()
                got += 1
                print(f"[{got:4d}] {size/1048576:6.2f} Mo  {dest.relative_to(CORPUS)}")
                if limit and got >= limit:
                    return
            except urllib.error.HTTPError as e:
                print(f"  HTTP {e.code} {name[:50]}")
                failed += 1
            except Exception as e:
                print(f"  {type(e).__name__} {name[:50]}")
                failed += 1
            time.sleep(SLEEP)
    print(f"\ndone: {got} files, {skipped} skipped, {failed} failures in {(time.time()-t0)/60:.1f} min")
    print(f"corpus: {sum(f.stat().st_size for f in CORPUS.rglob('*') if f.is_file())/1024**3:.2f} Go")


def status():
    files = [f for f in CORPUS.rglob("*") if f.is_file() and f.name != "manifest.jsonl"]
    by_ext = {}
    for f in files:
        by_ext[f.suffix.lower()] = by_ext.get(f.suffix.lower(), 0) + 1
    print(f"{len(files)} files, {sum(f.stat().st_size for f in files)/1024**3:.2f} Go")
    print(json.dumps(by_ext, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--semester")
    ap.add_argument("--branch")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    status() if a.status else fetch(a.limit, a.semester, a.branch)
