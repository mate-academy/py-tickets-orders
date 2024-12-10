from typing import Type

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    MovieListSerializer, OrderSerializer,
)


def _params_to_int(param: str) -> list:
    return [int(str_id) for str_id in param.split(",")]


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

    def get_serializer_class(self) -> Type[
        MovieListSerializer
        | MovieDetailSerializer
        | MovieSerializer
    ]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self) -> queryset:
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors = _params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actors)

        if genres:
            genres = _params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genres)

        if title:
            queryset = queryset.filter(title__contains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self) -> Type[
        MovieSessionListSerializer
        | MovieSessionDetailSerializer
        | MovieSessionSerializer
    ]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self) -> queryset:
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset.
                select_related("cinema_hall", "movie").
                annotate(
                    tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        if self.action == "retrieve":
            queryset = queryset.select_related("cinema_hall", "movie")

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie:
            movie = _params_to_int(movie)
            queryset = queryset.filter(movie__id__in=movie)

        return queryset.distinct()


class OrderSetPagination(PageNumberPagination):
    page_size = 1
    page_query_param = "page"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self) -> queryset:
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
