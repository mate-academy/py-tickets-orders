from datetime import datetime

from django.db.models import F
from django.db.models.aggregates import Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.serializers import (
    GenreSerializer,
    MovieSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    MovieListSerializer,
    OrderSerializer,
    OrderListSerializer,
    CinemaHallSerializer,
    MovieSessionSerializer,
)


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("actors", "genres")
    serializer_class = MovieSerializer

    @staticmethod
    def params_to_ints(query_string: str) -> list[int]:
        try:
            return [int(param) for param in query_string.split(",")]
        except ValueError:
            return []

    def get_queryset(self):
        queryset = self.queryset
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if actors:
            actors = self.params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors)

        if genres:
            genres = self.params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return self.serializer_class


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset.annotate(
            tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets")
            )
        )
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=int(movie))

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return self.serializer_class


class OrderSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
