from django.urls import path, include
from rest_framework import routers

from cinema.views import (
    GenreViewSet,
    ActorViewSet,
    CinemaHallViewSet,
    MovieViewSet,
    MovieSessionViewSet,
    OrderListViewSet,
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet, basename="genres")
router.register("actors", ActorViewSet, basename="actors")
router.register("cinema_halls", CinemaHallViewSet, basename="cinema_halls")
router.register("movies", MovieViewSet, basename="movies")
router.register(
    "movie_sessions", MovieSessionViewSet, basename="movie_session"
)
router.register("orders", OrderListViewSet, basename="orders")

urlpatterns = [path("", include(router.urls))]

app_name = "cinema"
