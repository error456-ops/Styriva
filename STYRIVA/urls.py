
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect

from django.conf import settings
from django.conf.urls.static import static
from django.templatetags.static import static as static_url
from django.views.generic import TemplateView


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def favicon_redirect(request):
    return redirect(static_url("favicon.ico"), permanent=True)


urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),

    path("manifest.webmanifest", TemplateView.as_view(
        template_name="manifest.webmanifest",
        content_type="application/manifest+json"), name="manifest"),

    path("sw.js", TemplateView.as_view(
        template_name="sw.js",
        content_type="application/javascript"), name="sw"),

    path("robots.txt", robots_txt),
    path("favicon.ico", favicon_redirect),

    path("", include("selfmirror.urls")),
]

# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )