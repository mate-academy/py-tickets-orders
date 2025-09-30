from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("cinema.urls")),
]

if settings.DEBUG:
    try:
        import debug_toolbar  # type: ignore
    except Exception:
        pass
    else:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
