from django.urls import path, include
from rest_framework import routers

from cinema.views import (
    GenreViewSet,
    ActorViewSet,
    CinemaHallViewSet,
    MovieViewSet,
    MovieSessionViewSet,
    OrderListCreateView,
    MovieSessionDetailView,
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("cinema_halls", CinemaHallViewSet)
router.register("movies", MovieViewSet)
router.register("movie_sessions", MovieSessionViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path(
        "movie_sessions/<int:pk>/",
        MovieSessionDetailView.as_view(),
        name="movie-session-detail",
    ),
]

app_name = "cinema"
