
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView

from django.conf import settings
from django.conf.urls.static import static
from django.templatetags.static import static as static_url
from django.contrib.staticfiles import finders


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
    ]
    return HttpResponse(
        "\n".join(lines),
        content_type="text/plain"
    )


def favicon_redirect(request):
    return redirect(
        static_url("favicon.ico"),
        permanent=True
    )


def serve_service_worker(request):
    worker_path = finders.find("service-worker.js")

    if not worker_path:
        raise Http404("Service worker not found")

    with open(worker_path, "r", encoding="utf-8") as file:
        response = HttpResponse(
            file.read(),
            content_type="application/javascript"
        )

    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"

    return response


urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),

    # PWA manifest
    path(
        "manifest.webmanifest",
        TemplateView.as_view(
            template_name="manifest.webmanifest",
            content_type="application/manifest+json"
        ),
        name="manifest"
    ),

    # PWA service worker
    path(
        "sw.js",
        serve_service_worker,
        name="sw"
    ),

    # Offline page
    path(
        "offline/",
        TemplateView.as_view(
            template_name="offline.html"
        ),
        name="offline"
    ),

    path("robots.txt", robots_txt),
    path("favicon.ico", favicon_redirect),

    path("", include("selfmirror.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
