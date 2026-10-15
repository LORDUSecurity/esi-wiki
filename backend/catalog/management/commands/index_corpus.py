"""Index the wiki's documents so the assistant can quote them.

Two roots are read: the mirrored EsiHub corpus (`corpus/`) and the repo's own lecture files
(`courses/`, already catalogued by `seed_catalog`).

  python manage.py index_corpus              # whatever is on disk, skipping what's done
  python manage.py index_corpus --rebuild    # drop the index and redo everything
  python manage.py index_corpus --limit 30   # try it on a few files
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog import corpus
from catalog.models import CorpusChunk, CorpusDoc


class Command(BaseCommand):
    help = "Extract text from corpus/ and courses/ and index it for the assistant (SQLite FTS5)."

    def add_arguments(self, parser):
        parser.add_argument("--rebuild", action="store_true", help="re-index every file")
        parser.add_argument("--limit", type=int, help="stop after N documents")

    def handle(self, *args, **opts):
        if not corpus.available():
            self.stdout.write(
                self.style.WARNING(
                    "No corpus folder (python tools/esihub_fetch.py downloads it) — "
                    "indexing the repo's own courses/ only."
                )
            )
        self.stdout.write(f"Indexing {corpus.corpus_root()} and {settings.MEDIA_ROOT} …")
        total = corpus.sync_index(limit=opts["limit"], rebuild=opts["rebuild"])
        self.stdout.write(self.style.SUCCESS(
            f"{total['documents']} documents, {total['chunks']} chunks"
            + (f", {total.get('empty', 0)} without extractable text" if total.get("empty") else "")
        ))
        self.stdout.write(
            f"totals: {CorpusDoc.objects.count()} docs, "
            f"{CorpusChunk.objects.count()} chunks indexed"
        )
