from typing import Type

from django.db.models import Count, F
from rest_framework import viewsets
from cinema.function import params_to_int

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
)

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
from cinema.pagination import OrderPagination


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

    # @staticmethod
    # def params_to_int(string: str) -> list:
    #     return [int(str_id) for str_id in string.split(",")]

    def get_queryset(self) -> queryset:
        queryset = super().get_queryset()

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")
        return queryset.distinct()

    def get_serializer_class(self) -> Type[MovieSerializer | MovieSerializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> queryset:
        queryset = super().get_queryset()

        movie = self.request.query_params.get("movie")
        if movie:
            movies_ids = params_to_int(movie)
            queryset = queryset.filter(movie__id__in=movies_ids)

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related(
                "movie",
                "cinema_hall").annotate(
                tickets_available=F(
                    "cinema_hall__rows"
                ) * F("cinema_hall__seats_in_row") - Count("tickets")
            ).order_by("id")

        return queryset.distinct()

    def get_serializer_class(self) -> Type[MovieSessionSerializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> queryset:
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
        return queryset

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
