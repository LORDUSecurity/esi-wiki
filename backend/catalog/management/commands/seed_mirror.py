"""Turn the mirrored EsiHub corpus (corpus/S3..S5) into first-class catalogue content.

Idempotent: it only replaces the rows it owns (origin="esihub"), so `seed_catalog` — which
builds S1-S2 from the cloned courses/ folder — stays untouched.
"""
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import CorpusDoc, HubCourse, Module, Resource, Semester
from catalog.management.commands.seed_catalog import kind_of

# S1 and S2 come from the repo's own PDFs; this command owns the mirrored semesters.
MIRROR_SEMESTERS = ["S3", "S4", "S5"]

# CorpusDoc.kind carries EsiHub's labels, Resource.kind the wiki's.
KIND_MAP = {"cours": "cours", "examen": "exam", "resume": "resume", "tp": "tp", "td": "td"}

# A Drive folder named "module" holds a whole filière semester unsplit; those files
# become one documents module rather than being dropped on the floor.
FLAT_CODES = {"module", ""}

# EsiHub lists a course as "M.3.1.1 - UML" or "3- Veille stratégique".
LEADING_CODE = re.compile(r"^\s*[A-Za-z0-9][A-Za-z0-9.+/\-]*\s*[-–]\s*")
# Some rows merge two units: "2.1 - Java+ 2.2 - Projet OO".
MERGED_CODE = re.compile(r"\s+\d+(?:\.\d+)?\s*[-–]\s+")


def fold(text):
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(c)
    ).lower()


def course_name(title):
    name = LEADING_CODE.sub("", title).strip()
    return MERGED_CODE.sub(" · ", name).strip() or title


def kind_for(folder_kind, name):
    """Drive folders say cours / examen / resume; a file named "TD1 - ..." or "TP N°3" says more.

    Only those three markers override, because a résumé folder legitimately holds files whose
    title starts with "Cours de …", and the folder label is the curated one.
    """
    kind = KIND_MAP.get(folder_kind, "autre")
    named = kind_of(name)
    return named if named in ("tp", "td", "exam") else kind


def block_of(code, semester=""):
    """Which of the eight blocs a mirrored unit belongs to.

    EsiHub numbers units two different ways: "4.2" is bloc 4, and "M.<a>.<b>" is either
    M.<semestre>.<bloc> (S3, S4) or M.<bloc>.<unité> (S5). The semester digit tells them apart.
    """
    groups = [int(g) for g in re.findall(r"\d+", str(code))]
    if not groups:
        return 0
    sem = int(re.sub(r"\D", "", str(semester)) or 0)
    if str(code)[0].isalpha():
        number = groups[-1] if len(groups) > 1 and groups[0] == sem else groups[0]
    else:
        number = groups[0]
    return number if 1 <= number <= 8 else 0


class Command(BaseCommand):
    help = "Index the mirrored EsiHub documents (S3-S5) as modules and resources."

    def add_arguments(self, parser):
        parser.add_argument("--root", default=str(Path(settings.CORPUS_DIR)))
        parser.add_argument(
            "--semesters",
            default=",".join(MIRROR_SEMESTERS),
            help="Comma-separated semesters to (re)build, e.g. S3,S4,S5",
        )

    def handle(self, *args, **opts):
        root = Path(opts["root"])
        if not root.is_dir():
            self.stderr.write(
                self.style.ERROR(f"No corpus folder at {root} — run tools/esihub_fetch.py first.")
            )
            return

        wanted = [s.strip().upper() for s in opts["semesters"].split(",") if s.strip()]

        # One Drive folder covers several EsiHub courses (M.3.1 = projet SI + UML), so keep
        # every name for a code instead of the last one written.
        by_code = {}
        units = {}
        for course in HubCourse.objects.all():
            key = (course.branch, course.semester)
            name = course_name(course.title)
            if course.code:
                names = by_code.setdefault(key + (course.code,), [])
                if name not in names:
                    names.append(name)
            else:
                # Filieres listed without codes: still the module list of that semester.
                if name not in units.setdefault(key, []):
                    units[key].append(name)

        Module.objects.filter(origin="esihub").delete()

        buckets = {}
        for doc in CorpusDoc.objects.filter(semester__in=wanted).order_by(
            "semester", "branch", "module_code", "name"
        ):
            buckets.setdefault((doc.branch, doc.semester, doc.module_code), []).append(doc)

        modules = resources = missing = 0
        for (branch, semester, folder_code), docs in buckets.items():
            sem = Semester.objects.filter(code=semester).first()
            if sem is None:
                sem = Semester.objects.create(
                    code=semester, title=f"Semestre {semester[1:]}", order=int(semester[1:])
                )

            flat = fold(folder_code) in FLAT_CODES
            code = "DOC" if flat else folder_code.strip()
            if flat:
                title = f"Documents {branch} {semester}"
                block = 0
            else:
                names = by_code.get((branch, semester, code), [])
                title = " · ".join(names[:4]) if names else f"{branch} {semester} {code}"
                block = block_of(code, semester)

            module = Module.objects.create(
                code=code[:16],
                title=title[:200],
                slug=slugify(f"{semester}-{branch}-{code}-{title}")[:220],
                semester=sem,
                block=block,
                branch=branch,
                origin="esihub",
                folder=f"{semester}/{branch}/{folder_code}",
                summary=self.summary(branch, semester, code, flat, len(docs), units.get((branch, semester), [])),
                tags=[branch],
            )
            modules += 1

            for doc in docs:
                if not (root / doc.path).is_file():
                    # Still catalogued: without the local copy the link falls back to Drive.
                    missing += 1
                Resource.objects.create(
                    module=module,
                    title=doc.name[:300],
                    path=doc.path,
                    kind=kind_for(doc.kind, doc.name),
                    origin="esihub",
                    drive_id=doc.drive_id,
                    file_type=Path(doc.name).suffix.lower().lstrip("."),
                    size_kb=max(1, doc.bytes // 1024),
                )
                resources += 1

        note = f"Seeded {modules} mirrored modules / {resources} resources"
        if missing:
            note += f" — {missing} of them are not on disk, so they link to Drive"
        self.stdout.write(self.style.SUCCESS(note))

    @staticmethod
    def summary(branch, semester, code, flat, count, semester_units):
        # Baked into a database that travels into the sample, where the files are not: say how a
        # document opens, not where the copy lives.
        if flat:
            listed = ", ".join(semester_units[:10]) if semester_units else ""
            return (
                f"{count} documents EsiHub de la filière {branch} ({semester}), regroupés ici "
                "parce que le dossier Drive n'est pas découpé par module. Chacun s'ouvre depuis "
                "cette page, ou depuis son Drive d'origine."
                + (f" Ils couvrent : {listed}." if listed else "")
            )
        return (
            f"Module {code} de la filière {branch} ({semester}). {count} documents EsiHub — "
            "polycopiés, TD, annales, résumés — relevés sur esihub.net et ouverts depuis cette page."
        )
