from typing import Type

from django.db.models import QuerySet, F, Count
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
    OrderCreateSerializer,
    OrderListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    @staticmethod
    def _params_to_ints(param_str) -> list:
        return [
            int(param)
            for param in
            param_str.split(",")
        ]

    def get_queryset(self):
        params = self.request.query_params
        actors = params.get("actors")
        if actors:
            actors_ids = self._params_to_ints(actors)
            self.queryset = self.queryset.filter(
                actors__id__in=actors_ids
            )

        genres = params.get("genres")
        if genres:
            genres_ids = self._params_to_ints(genres)
            self.queryset = self.queryset.filter(
                genres__id__in=genres_ids
            )
        title = params.get("title")
        if title:
            self.queryset = self.queryset.filter(
                title__icontains=title
            )

        return self.queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self):
        if self.action == "list":
            self.queryset = (
                self.queryset.select_related("cinema_hall", "movie")
                .prefetch_related("tickets")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )
            params = self.request.query_params
            date = params.get("date")
            if date:
                self.queryset = self.queryset.filter(
                    show_time__date=date
                )

            id_ = params.get("movie")
            if id_:
                self.queryset = self.queryset.filter(
                    movie__pk=int(id_)
                )
        return self.queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_serializer_class(self) -> Type[Serializer]:
        serializer_class = OrderSerializer
        if self.action in ("list", "retrieve"):
            serializer_class = OrderListSerializer
        elif self.action == "create":
            serializer_class = OrderCreateSerializer

        return serializer_class

    def get_queryset(self) -> QuerySet[Order]:
        queryset = Order.objects.filter(
            user=self.request.user
        )
        if self.action in ("retrieve", "list"):
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie"
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
