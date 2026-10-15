"""Enumerate (and later fetch) the Google Drive folders EsiHub points at.

EsiHub lists each module as a folder link; Drive renders the children in the
`folderview` HTML, so we read them from there: no Drive API, no token, nothing to leak.

  python tools/esihub_drive.py probe --folders 12     # size the corpus before downloading
  python tools/esihub_drive.py list <folder-id>
"""

import argparse
import html
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
FOLDER_URL = "https://drive.google.com/folderview?id={}"
DOWNLOAD_URL = "https://drive.usercontent.google.com/download?id={}&export=download&confirm=t"

# <div … aria-label="Cours GED-1.pdf PDF Shared" … ssk='5:<sig>:<file-id>-0-16'>
# Drive ids contain '-' themselves, so the id is everything before the trailing "-<n>-<n>".
ENTRY_RE = re.compile(
    r'aria-label="(?P<name>[^"]+?) (?P<kind>(?:PDF|Image|Text file|Zip archive|Microsoft [^"]*|'
    r'Google [^"]*|Audio|Video|Unknown|Folder) Shared)"'
    r"[^>]*ssk='\d+:[A-Za-z0-9_-]+:(?P<id>[A-Za-z0-9_-]{20,})-\d+-\d+"
)


def _get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout)


def list_folder(folder_id):
    """[(name, id, is_folder)] for one public Drive folder."""
    page = _get(FOLDER_URL.format(folder_id)).read().decode("utf-8", "replace")
    out = []
    for m in ENTRY_RE.finditer(page):
        kind = "folder" if m.group("kind").startswith("Folder") else "file"
        # Drive escapes the labels it renders ("d&#39;anxiété.pdf"); the name goes into filenames
        # and into the citations students read, so unescape it here rather than everywhere later.
        out.append((html.unescape(m.group("name")), m.group("id"), kind))
    return out


def size_of(file_id):
    """Content-Length of a file, without pulling the whole body down."""
    try:
        r = _get(DOWNLOAD_URL.format(file_id), timeout=40)
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    try:
        length = int(r.headers.get("Content-Length") or 0) or None
    except ValueError:
        length = None
    finally:
        r.close()
    return length, None


def all_folders(semester=None, branch=None, kind=None):
    import django, os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    from catalog.models import HubCourse

    qs = HubCourse.objects.all()
    if semester:
        qs = qs.filter(semester=semester)
    if branch:
        qs = qs.filter(branch=branch)
    for c in qs:
        for k, url in (c.links or {}).items():
            if kind and k != kind:
                continue
            m = re.search(r"/folders/([A-Za-z0-9_-]{10,})", url or "")
            if m:
                yield m.group(1), (c.code, c.title, c.semester, c.branch, k)


def probe(count, seed=7, verbose=True):
    folders = {}
    for fid, meta in all_folders():
        folders.setdefault(fid, meta)
    picks = random.Random(seed).sample(list(folders.items()), min(count, len(folders)))
    rows, total_files = [], 0
    for fid, meta in picks:
        try:
            entries = list_folder(fid)
        except Exception as e:
            rows.append((meta, None, f"{type(e).__name__}"))
            continue
        files = [e for e in entries if e[2] == "file"]
        total_files += len(files)
        rows.append((meta, len(files), None))
        if verbose:
            print(f"{'/'.join(str(x) for x in meta):52s} {len(files):3d} files")
        time.sleep(0.35)
    measured = [r for r in rows if r[1] is not None]
    mean = sum(r[1] for r in measured) / len(measured) if measured else 0
    sizes = []
    for meta, n, _ in measured[:3]:
        fid = [f for f, m in folders.items() if m == meta][0]
        for name, i, _k in list_folder(fid)[:2]:
            length, err = size_of(i)
            if length:
                sizes.append(length)
            time.sleep(0.3)
    mean_bytes = sum(sizes) / len(sizes) if sizes else 0
    print(json.dumps({
        "folders_total": len(folders),
        "sampled": len(measured),
        "mean_files_per_folder": round(mean, 2),
        "projected_files": int(mean * len(folders)),
        "sample_file_sizes_mb": [round(s / 1048576, 2) for s in sizes],
        "mean_file_mb": round(mean_bytes / 1048576, 2),
        "projected_gb": round(mean * len(folders) * mean_bytes / 1024**3, 2) if mean_bytes else None,
    }, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("--folders", type=int, default=12)
    l = sub.add_parser("list")
    l.add_argument("folder_id")
    a = ap.parse_args()
    if a.cmd == "probe":
        probe(a.folders)
    else:
        for name, i, kind in list_folder(a.folder_id):
            print(f"{kind:6s} {i:33s} {name}")


if __name__ == "__main__":
    main()
