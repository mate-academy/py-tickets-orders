from datetime import datetime

from django.db.models import Q, Count, F
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
    MovieListSerializer,
    OrderSerializer,
    OrderListSerializer,
)


def type_converter(data: str) -> list:
    return [int(char_id) for char_id in data.split(",")]


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

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("actors", "genres")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        conditions = Q()

        if actors:
            conditions &= Q(actors__id__in=type_converter(actors))

        if genres:
            conditions &= Q(genres__id__in=type_converter(genres))

        if title:
            conditions &= Q(title__icontains=title)

        return queryset.filter(conditions)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset.
                select_related("movie", "cinema_hall")
                .annotate(tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets"))
                )
            )
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        conditions = Q()

        if date:
            conditions &= Q(
                show_time__contains=datetime.strptime(
                    date, "%Y-%m-%d"
                ).date()
            )
        if movie:
            conditions &= Q(movie__id__in=type_converter(movie))

        return queryset.filter(conditions)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderListPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (
        Order.objects.
        select_related("user")
        .prefetch_related(
            "tickets",
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie"
        )
    )
    serializer_class = OrderSerializer
    pagination_class = OrderListPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
