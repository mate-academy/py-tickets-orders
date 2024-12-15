from django.urls import include, path
from rest_framework import routers

from cinema.views import (ActorViewSet, CinemaHallViewSet, GenreViewSet,
                          MovieSessionViewSet, MovieViewSet, OrderViewSet)

router = routers.DefaultRouter()
router.register("orders", OrderViewSet)
router.register("movie_sessions", MovieSessionViewSet)
router.register("movies", MovieViewSet)
router.register("cinema_halls", CinemaHallViewSet)
router.register("actors", ActorViewSet)
router.register("genres", GenreViewSet)

urlpatterns = [
    path("", include(router.urls))
]

app_name = "cinema"
