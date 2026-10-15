import unicodedata

from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    CorpusChunk,
    CorpusDoc,
    HubCourse,
    HubReport,
    Module,
    Resource,
    Semester,
)
from .serializers import (
    HubCourseSerializer,
    HubReportSerializer,
    ModuleDetailSerializer,
    ModuleListSerializer,
    SemesterSerializer,
)


def _fold(text):
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(c)
    ).lower()


def _matches(term, *haystacks):
    """Accent-insensitive search. SQLite's icontains folds case but not accents, so
    "reseau" returned nothing against a catalogue that spells "Réseaux". These tables
    hold a few hundred rows, so the fold happens in Python instead of SQL."""
    needle = _fold(term)
    return any(needle in _fold(hay or "") for hay in haystacks)


@api_view(["GET"])
def health(request):
    return Response({
        "status": "ok",
        "modules": Module.objects.count(),
        "resources": Resource.objects.count(),
    })


@api_view(["GET"])
def semesters(request):
    data = Semester.objects.annotate(module_count=Count("modules"))
    return Response(SemesterSerializer(data, many=True).data)


@api_view(["GET"])
def modules(request):
    qs = Module.objects.select_related("semester")
    semester = request.query_params.get("semester")
    block = request.query_params.get("block")
    branch = request.query_params.get("branch")
    search = request.query_params.get("search")

    if semester:
        qs = qs.filter(semester__code=semester)
    if block:
        qs = qs.filter(block=block)
    if branch:
        qs = qs.filter(branch=branch)
    qs = qs.annotate(resource_count=Count("resources"))
    if search:
        # A module matches on its own title/code or on any document it carries.
        qs = [
            m
            for m in qs.prefetch_related("resources")
            if _matches(search, m.title, m.code, m.branch)
            or any(_matches(search, r.title) for r in m.resources.all())
        ]
    return Response(ModuleListSerializer(qs, many=True).data)


@api_view(["GET"])
def module_detail(request, slug):
    module = (
        Module.objects.select_related("semester")
        .prefetch_related("resources")
        .filter(slug=slug)
        .first()
    )
    if not module:
        return Response({"detail": "Module introuvable."}, status=404)
    data = ModuleDetailSerializer(module).data
    # EsiHub indexes the same modules for several filières; link out by code + semester.
    # The module's own filière is left out — its documents are already listed above.
    related = HubCourse.objects.filter(code=module.code, semester=module.semester.code)
    if module.branch:
        related = related.exclude(branch=module.branch)
    data["hub_references"] = HubCourseSerializer(related[:6], many=True).data
    return Response(data)


@api_view(["GET"])
def hub_courses(request):
    qs = HubCourse.objects.all()
    branch = request.query_params.get("branch")
    semester = request.query_params.get("semester")
    search = request.query_params.get("search")

    if branch:
        qs = qs.filter(branch=branch)
    if semester:
        qs = qs.filter(semester=semester)
    if search:
        qs = [c for c in qs if _matches(search, c.title, c.code)]
    return Response(HubCourseSerializer(qs, many=True).data)


@api_view(["GET"])
def hub_reports(request):
    qs = HubReport.objects.all()
    search = request.query_params.get("search")
    promotion = request.query_params.get("promotion")
    language = request.query_params.get("language")

    if promotion:
        qs = qs.filter(promotion=promotion)
    if language:
        qs = qs.filter(language=language)
    if search:
        qs = [
            r
            for r in qs
            if _matches(search, r.title, r.engineer, r.organisation, " ".join(r.tags or []))
        ]
    return Response(HubReportSerializer(qs, many=True).data)


@api_view(["GET"])
def hub_meta(request):
    courses = list(HubCourse.objects.all())
    branches, semesters = {}, {}
    for course in courses:
        branches[course.branch] = branches.get(course.branch, 0) + 1
        semesters[course.semester] = semesters.get(course.semester, 0) + 1
    reports = list(HubReport.objects.all())
    return Response({
        "source": "esihub.net",
        "courses": len(courses),
        "drive_links": sum(course.link_count for course in courses),
        "branches": [{"code": k, "courses": v} for k, v in sorted(branches.items())],
        "semesters": [{"code": k, "courses": v} for k, v in sorted(semesters.items())],
        "reports": len(reports),
        "report_links": sum(1 for r in reports if r.report_url),
        "promotions": sorted({r.promotion for r in reports if r.promotion}, reverse=True),
    })


@api_view(["GET"])
def stats(request):
    # Coverage means both catalogues, not just this repo's PDF folder: the mirrored EsiHub
    # corpus fills S3-S5, and S6 is the PFE year — no modules there, only the stage reports.
    indexed = {c.semester for c in HubCourse.objects.only("semester")} | set(
        Semester.objects.values_list("code", flat=True)
    )
    mirrored = Resource.objects.filter(origin="esihub")
    return Response({
        "modules": Module.objects.count(),
        "resources": Resource.objects.count(),
        "mirrored_modules": Module.objects.filter(origin="esihub").count(),
        "mirrored_documents": mirrored.count(),
        "branches": [
            {"code": row["branch"], "modules": row["n"]}
            for row in Module.objects.exclude(branch="")
            .values("branch")
            .annotate(n=Count("id"))
            .order_by("branch")
        ],
        "semesters_indexed": len(indexed),
        "pfe_reports": HubReport.objects.count(),
        # The engineering cycle runs S1..S6.
        "cycle_semesters": 6,
        # Mirrored EsiHub documents the assistant can quote; 0 in the shared sample build.
        "corpus_documents": CorpusDoc.objects.count(),
        "corpus_chunks": CorpusChunk.objects.count(),
        "documents_mb": round(sum(r.size_kb for r in Resource.objects.only("size_kb")) / 1024),
    })
