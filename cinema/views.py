from datetime import datetime
from typing import Type

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.serializers import Serializer

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_list_ints(qs: str) -> list:
        return [int(int_id) for int_id in qs.split(",")]

    def get_queryset(self) -> QuerySet:
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            genres = self._params_to_list_ints(genres)
            self.queryset = self.queryset.filter(genres__id__in=genres)
            return self.queryset.distinct()

        if actors:
            actors = self._params_to_list_ints(actors)
            self.queryset = self.queryset.filter(actors__id__in=actors)
            return self.queryset.distinct()

        if title:
            self.queryset = self.queryset.filter(title__icontains=title)
            return self.queryset.distinct()

        return self.queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        show_time = self.request.query_params.get("show_time")
        movie = self.request.query_params.get("movie")
        if show_time and movie:
            show_time = datetime.strptime(show_time, "%Y-%m-%d")
            self.queryset = self.queryset.filter(
                show_time__date=show_time.date()
            ).filter(movie_id=int(movie))
            return self.queryset.select_related("movie", "cinema_hall")
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie"
        )

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(user=self.request.user)
