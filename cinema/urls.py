from django.urls import path, include
from rest_framework import routers

from cinema.views import (
    GenreViewSet,
    ActorViewSet,
    CinemaHallViewSet,
    MovieViewSet,
    MovieSessionViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("cinema_halls", CinemaHallViewSet)
router.register("movies", MovieViewSet, basename="movie")
router.register(
    "movie_sessions", MovieSessionViewSet, basename="movie_session"
)
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [path("", include(router.urls))]

app_name = "cinema"
