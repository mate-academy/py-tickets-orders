from django.db.models import F, Model
from django.db.models.aggregates import Count
from django.db.models.query import Prefetch
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
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
    OrderListSerializer,
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
    def parse_query_params(params: str | None) -> list[int] | None:
        if params is None:
            return None
        return [int(id_) for id_ in params.split(",")]

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = MovieListSerializer

        if self.action == "retrieve":
            serializer = MovieDetailSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")
            if self.action == "list":
                actors = self.parse_query_params(
                    self.request.query_params.get("actors")
                )
                if actors:
                    queryset = queryset.filter(actors__id__in=actors)

                genres = self.parse_query_params(
                    self.request.query_params.get("genres")
                )
                if genres:
                    queryset = queryset.filter(genres__id__in=genres)

                title = self.request.query_params.get("title")
                if title:
                    queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = MovieSessionListSerializer

        if self.action == "retrieve":
            serializer = MovieSessionDetailSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("movie", "cinema_hall")
            if self.action == "list":
                queryset = queryset.annotate(
                    tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    )
                    - Count("tickets")
                )

                date = self.request.query_params.get("date")
                if date:
                    queryset = queryset.filter(show_time__date=date)

                movie = self.request.query_params.get("movie")
                if movie:
                    queryset = queryset.filter(movie=movie)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderListSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(user=self.request.user)

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")

        if self.action == "list":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "movie_session__movie",
                        "movie_session__cinema_hall",
                    ),
                )
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
