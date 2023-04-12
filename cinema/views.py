from django.db.models import F, Count
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
    OrderListSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def str_to_ids(string: str) -> list:
    return [int(char) for char in string.split(",")]


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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("actors", "genres")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = str_to_ids(actors)
            queryset = queryset.filter(actors__in=actors_ids)
        if genres:
            genres_ids = str_to_ids(genres)
            queryset = queryset.filter(genres__in=genres_ids)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.select_related("cinema_hall", "movie")

        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie:
            movie_ids = str_to_ids(movie)
            queryset = queryset.filter(movie__in=movie_ids)
        if date:
            queryset = queryset.filter(show_time__contains=date)
        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(F("cinema_hall__rows")
                                   * F("cinema_hall__seats_in_row")
                                   - Count("tickets"))
            )
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("tickets", "tickets__movie_session")

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
