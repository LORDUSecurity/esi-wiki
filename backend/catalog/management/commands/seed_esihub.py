"""Load the EsiHub crawl into the database.

Refresh the file first with `node tools/fetch-esihub.mjs` — the documents stay on
Google Drive, so these tables only hold links out to esihub.net.
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.models import HubCourse, HubReport

DEFAULT_FILE = settings.REPO_ROOT / "tools" / "esihub-catalog.json"


class Command(BaseCommand):
    help = "Importe l'index de esihub.net : cours (liens Drive) et rapports de PFE."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(DEFAULT_FILE), help="JSON produit par le crawl")

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_file():
            raise CommandError(f"{path} introuvable — lancez `node tools/fetch-esihub.mjs`.")

        payload = json.loads(path.read_text(encoding="utf-8"))

        # A course can legitimately appear twice in the crawl (same title, two promotions),
        # so the year is part of the key; report titles are unique.
        courses = [
            HubCourse(
                branch=row["branch"],
                semester=row["semester"],
                year=row.get("year", ""),
                code=row.get("code", ""),
                title=row["title"],
                links=row.get("links", {}),
            )
            for row in {
                (r["branch"], r["semester"], r.get("year", ""), r["title"]): r
                for r in payload["courses"]
            }.values()
        ]
        unique_reports = {}
        for row in payload.get("reports", []):
            kept = unique_reports.get(row["title"])
            # esihub lists a few reports twice, one copy without the Drive link.
            if kept and (kept.get("reportUrl") or not row.get("reportUrl")):
                continue
            unique_reports[row["title"]] = row
        reports = [
            HubReport(
                title=row["title"],
                engineer=row.get("engineer", ""),
                organisation=row.get("organisation", ""),
                promotion=row.get("promotion", ""),
                language=row.get("language", ""),
                tags=row.get("tags", []),
                abstract=row.get("abstract", ""),
                report_url=row.get("reportUrl", ""),
                page=row.get("page", ""),
            )
            for row in unique_reports.values()
        ]

        HubCourse.objects.all().delete()
        HubReport.objects.all().delete()
        HubCourse.objects.bulk_create(courses, batch_size=200)
        HubReport.objects.bulk_create(reports, batch_size=100)

        links = sum(len(c.links) for c in courses)
        branches = sorted({c.branch for c in courses})
        crawled = payload.get("meta", {}).get("crawled", "?")[:10]
        self.stdout.write(self.style.SUCCESS(
            f"{len(courses)} cours ({links} liens Drive) dans {', '.join(branches)}\n"
            f"{len(reports)} rapports de PFE — crawl du {crawled}"
        ))
