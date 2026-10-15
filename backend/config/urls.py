from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve

from catalog.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/", include("catalog.urls")),
    path("api/", include("core.urls")),
    path("api/", include("aichat.urls")),
]

# The cloned repo already carries the lecture PDFs; expose them under /courses/.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Mirrored EsiHub documents (S3-S5) live in corpus/, which is gitignored but shipped whole
# to anyone who runs the wiki locally; they are served under /polycopies/.
urlpatterns += [
    re_path(r"^polycopies/(?P<path>.*)$", serve, {"document_root": str(settings.CORPUS_DIR)}),
]

dist = settings.FRONTEND_DIST
if dist.exists():
    # Vite copies public/ into dist/, so the gallery photos are served from there too.
    urlpatterns += [
        re_path(r"^assets/(?P<path>.*)$", serve, {"document_root": str(dist / "assets")}),
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": str(dist / "media")}),
    ]
    urlpatterns += [
        re_path(
            r"^(?!api/|admin/|courses/|polycopies/|assets/|static/).*$",
            lambda request: FileResponse(open(dist / "index.html", "rb"), content_type="text/html"),
        )
    ]
else:
    urlpatterns += [
        re_path(
            r"^.*$",
            lambda request: JsonResponse(
                {"detail": "Frontend not built yet. Run `npm run build` in frontend/, or use the Vite dev server on :5173."},
                status=503,
            ),
        )
    ]
