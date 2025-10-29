from django.urls import path, include
from rest_framework.routers import DefaultRouter

from cinema.views import (
    OrderViewSet,
    MovieViewSet,
    MovieSessionViewSet,
    GenreViewSet,
    ActorViewSet,
    CinemaHallViewSet,
)

app_name = "cinema"

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"movies", MovieViewSet, basename="movie")
router.register(
    r"movie_sessions",
    MovieSessionViewSet,
    basename="movie-session",
)
router.register(r"genres", GenreViewSet, basename="genre")
router.register(r"actors", ActorViewSet, basename="actor")
router.register(r"cinema_halls", CinemaHallViewSet, basename="cinema-hall")

urlpatterns = [
    path("", include(router.urls)),
]
