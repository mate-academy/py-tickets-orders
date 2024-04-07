from django.db.models import Count, F
from rest_framework import viewsets

from cinema.models import Genre, Actor, Movie, CinemaHall, MovieSession, Order
from cinema.paginations import OrderSetPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    MovieSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    CinemaHallSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    TicketSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


def convert_query_params_to_ints(query_string: str):
    """
    Convert a string of format '1,2,3' to a list of integers [1, 2, 3]
    """
    return [int(str_id) for str_id in query_string.split(",")]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "list":
            serializer_class = MovieListSerializer

        if self.action == "retrieve":
            serializer_class = MovieDetailSerializer

        return serializer_class

    def get_queryset(self):
        queryset = self.queryset

        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genres = convert_query_params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres)

        if actors:
            actors = convert_query_params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors", )

        return queryset


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "list":
            serializer_class = MovieSessionListSerializer

        if self.action == "retrieve":
            serializer_class = MovieSessionDetailSerializer

        return serializer_class

    def get_queryset(self):
        queryset = self.queryset

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie:
            movie = convert_query_params_to_ints(movie)
            queryset = queryset.filter(movie__id__in=movie)

        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall", )
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        if self.action == "retrieve":
            queryset = queryset.select_related("movie", "cinema_hall", )

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "create":
            serializer_class = OrderCreateSerializer

        return serializer_class

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action in ("list", "retrieve",):
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
