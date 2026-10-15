"""Stage the database the shared sample ships with: the dev copy, minus the mirrored text.

`tools/esihub_fetch.py` and `manage.py index_corpus` keep the polycopiés in ./corpus and their
extracted text in the database. The folder is not bundled, but the rows are — several megabytes
of other people's course documents travelling inside something the user zips and shares. The
sample answers from the catalogue and the rules; with the index dropped here, the retrieval tier
finds no `corpus_fts` table, its query fails quietly, and `search()` returns nothing.

    python packaging/strip-corpus.py      # -> build/sample-db/db.sqlite3
"""

import shutil
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "backend" / "db.sqlite3"
DST = REPO / "build" / "sample-db" / "db.sqlite3"

# FTS5 keeps its own copy of the same text, next to the rows, along with its shadow tables.
CORPUS_SQL = (
    "DELETE FROM catalog_corpuschunk",
    "DELETE FROM catalog_corpusdoc",
    "DROP TABLE IF EXISTS corpus_fts",
    "DROP TABLE IF EXISTS corpus_fts_data",
    "DROP TABLE IF EXISTS corpus_fts_idx",
    "DROP TABLE IF EXISTS corpus_fts_docsize",
    "DROP TABLE IF EXISTS corpus_fts_config",
)


def main():
    if not SRC.exists():
        print(f"no database at {SRC}", file=sys.stderr)
        return 1
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, DST)

    con = sqlite3.connect(DST)
    for sql in CORPUS_SQL:
        try:
            con.execute(sql)
        except sqlite3.OperationalError:
            # A database older than the corpus tables simply has nothing to strip.
            pass
    con.commit()
    con.execute("VACUUM")

    docs = con.execute("SELECT count(*) FROM catalog_corpusdoc").fetchone()[0]
    chunks = con.execute("SELECT count(*) FROM catalog_corpuschunk").fetchone()[0]
    con.close()

    print(
        f"staged {DST.name} in {DST.parent}: {DST.stat().st_size // 1024} Ko "
        f"(from {SRC.stat().st_size // 1024} Ko) — corpus rows left: {docs} docs / {chunks} chunks"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
