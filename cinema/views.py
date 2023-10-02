from rest_framework import viewsets
from django.db.models import Count, F

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

    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,

    MovieSerializer,
    MovieDetailSerializer,
    MovieListSerializer,

    OrderSerializer,
    OrderListSerializer,
)
from .pagination import OrderPagination


def get_ids(query_value: str) -> list[int]:
    return [int(value) for value in query_value.split(",")]


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
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_id = get_ids(actors)
            queryset = queryset.filter(actors__id__in=actors_id)

        if genres:
            genres_id = get_ids(genres)
            queryset = queryset.filter(genres__id__in=genres_id)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


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
        queryset = self.queryset
        date = self.request.query_params.get("date")
        movies = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movies:
            movies_id = get_ids(movies)
            queryset = queryset.filter(movie__id__in=movies_id)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "tickets", "movie__genres", "movie__actors"
            ).select_related(
                "cinema_hall"
            ).annotate(tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
            ).order_by("id")
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer
