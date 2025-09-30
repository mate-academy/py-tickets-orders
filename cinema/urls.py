# cinema/urls.py
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    ActorViewSet,
    CinemaHallViewSet,
    GenreViewSet,
    MovieSessionViewSet,
    MovieViewSet,
    OrderViewSet,
)


class OptionalSlashRouter(SimpleRouter):
    trailing_slash = "/?"


router = OptionalSlashRouter()
router.register(r"actors", ActorViewSet, basename="actor")
router.register(r"genres", GenreViewSet, basename="genre")
router.register(r"movies", MovieViewSet, basename="movie")

# Registrar COM underscore (o que os testes usam)…
router.register(r"cinema_halls", CinemaHallViewSet, basename="cinemahall")
router.register(r"movie_sessions", MovieSessionViewSet, basename="moviesession")
router.register(r"orders", OrderViewSet, basename="order")

# …e manter também a versão com hífen, só por conveniência no navegador
router.register(r"cinema-halls", CinemaHallViewSet, basename="cinemahall_dash")

urlpatterns = [
    path("api/cinema/", include((router.urls, "cinema"), namespace="cinema_api")),
    path("api/", include((router.urls, "cinema"), namespace="api")),
    path("", include(router.urls)),
]
