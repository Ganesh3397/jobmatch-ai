from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse, JsonResponse
from django.urls import include, path, re_path


def health(request):
    return JsonResponse({"status": "ok", "app": "JobMatch AI"})


def react_app(request):
    """Serve the built React app for every non-API URL (production, single domain)."""
    index = settings.FRONTEND_BUILD_DIR / "index.html"
    if index.exists():
        return FileResponse(open(index, "rb"), content_type="text/html")
    return HttpResponse("Frontend not built. In development open http://localhost:5173", status=404)


admin.site.site_header = "JobMatch AI - Admin"
admin.site.site_title = "JobMatch AI"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("accounts.urls")),
    path("api/resumes/", include("resumes.urls")),
    path("api/jobs/", include("jobs.urls")),
    path("api/analytics/", include("analytics.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
    re_path(r"^(?!api/|admin/|static/|media/).*$", react_app),
]
