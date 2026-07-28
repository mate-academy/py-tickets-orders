from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/cinema/", include("cinema.urls", namespace="cinema")),
    path(
        "api-auth/",
        include("rest_framework.urls", namespace="rest_framework")
    ),
    path("__debug__/", include("debug_toolbar.urls")),
]
