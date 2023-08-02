from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre, Actor,
    CinemaHall, Movie,
    MovieSession, Order
)

from cinema.serializers import (
    GenreSerializer, ActorSerializer,
    CinemaHallSerializer, MovieSerializer,
    MovieSessionSerializer, MovieSessionListSerializer,
    MovieDetailSerializer, MovieSessionDetailSerializer,
    MovieListSerializer, OrderListSerializer,
    OrderSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = self.get_ids_list(actors)
            queryset = queryset.filter(actors__in=actors_ids)

        if genres:
            genres_ids = self.get_ids_list(genres)
            queryset = queryset.filter(genres__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action == ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset.distinct()

    @staticmethod
    def get_ids_list(ids_str: str) -> list:
        return [int(str_id) for str_id in ids_str.split(",")]


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = (
            self.queryset
            .select_related("movie", "cinema_hall")
            .prefetch_related("tickets")
        )
        if self.action in ["list"]:
            queryset = queryset.select_related(
                "cinema_hall", "movie"
            ).annotate(tickets_available=(
                F("cinema_hall__seats_in_row") * F("cinema_hall__rows")
                - Count("tickets"))
            )
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if movie:
            queryset = queryset.filter(movie_id=movie)

        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):

    queryset = Order.objects.prefetch_related(
        "tickets",
        "tickets__movie_session__cinema_hall",
        "tickets__movie_session__movie"
    )
    serializer_class = OrderListSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
