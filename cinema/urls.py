from django.urls import include, path
from rest_framework import routers

from cinema.views import (ActorViewSet, CinemaHallViewSet, GenreViewSet,
                          MovieSessionViewSet, MovieViewSet, OrderViewSet)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet, basename="genres")
router.register("actors", ActorViewSet, basename="actors")
router.register("cinema_halls", CinemaHallViewSet, basename="cinema_halls")
router.register("movies", MovieViewSet, basename="movies")
router.register(
    "movie_sessions", MovieSessionViewSet, basename="movie_sessions"
)
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [path("", include(router.urls))]

app_name = "cinema"
