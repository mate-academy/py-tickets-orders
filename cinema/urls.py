from django.urls import path, include
from rest_framework import routers

from cinema.views import (
    GenreViewSet,
    ActorViewSet,
    CinemaHallViewSet,
    MovieViewSet,
    MovieSessionViewSet,
    OrderViewSet, TicketViewSet,
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("cinema_halls", CinemaHallViewSet)
router.register(
    "movies",
    MovieViewSet,
    basename="movies"
)
router.register(
    "movie_sessions",
    MovieSessionViewSet,
    basename="movie_sessions"
)
router.register("orders", OrderViewSet, basename="orders")
router.register("tickets", TicketViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "cinema"
