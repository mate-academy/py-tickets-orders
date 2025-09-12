from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/cinema/", include("cinema.urls", namespace="cinema")),
]

# Add debug_toolbar URLs only if enabled
if getattr(settings, "DEBUG_TOOLBAR_ENABLED", False):
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
