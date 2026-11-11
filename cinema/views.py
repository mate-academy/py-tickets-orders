from django.db.models import Prefetch, Count, F
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


def query_parsing(string_to_parse: str | None) -> list[int] | None:
    if string_to_parse:
        return [
            int(id_str)
            for id_str in string_to_parse.split(",")
            if id_str.isnumeric()
        ]


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
        queryset = super().get_queryset()

        actors = query_parsing(self.request.query_params.get("actors"))
        genres = query_parsing(self.request.query_params.get("genres"))
        title = self.request.query_params.get("title")

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

        if actors:
            queryset = queryset.filter(actors__id__in=actors)
        if genres:
            queryset = queryset.filter(genres__id__in=genres)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

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
        queryset = super().get_queryset()

        date = self.request.query_params.get("date")
        movie = query_parsing(self.request.query_params.get("movie"))

        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie__id__in=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_serializer_class(self):

        if self.action in ("list", "retrieve"):
            return OrderListSerializer

        return OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)

        if self.action in ("list", "retrieve"):
            movie_sessions_queryset = MovieSession.objects.select_related(
                "cinema_hall",
                "movie"
            )
            prefetch = Prefetch(
                "tickets__movie_session",
                queryset=movie_sessions_queryset
            )
            queryset = queryset.prefetch_related(prefetch)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
