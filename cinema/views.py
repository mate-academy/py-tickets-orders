from django.db.models import QuerySet, Q, F, Count
from rest_framework import viewsets
from rest_framework.serializers import Serializer, SerializerMetaclass

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
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
    OrderSetPagination,
    OrderCreateSerializer,
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

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.prefetch_related("actors", "genres")
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        if title:
            queryset = queryset.filter(
                title__icontains=title
            )

        if actors:
            actors = _get_params(actors)
            queryset = queryset.filter(
                actors__id__in=actors
            )

        if genres:
            genres = _get_params(genres)
            queryset = queryset.filter(
                genres__id__in=genres
            )

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

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.select_related("movie")
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(
                show_time__date=date
            )

        if movie:
            movie = _get_params(movie)
            queryset = queryset.filter(
                movie__id__in=movie
            )

        queryset = queryset.annotate(
            tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> SerializerMetaclass:
        if self.action == "list":
            return OrderSerializer

        if self.action == "create":
            return OrderCreateSerializer

        return OrderSerializer


def _get_params(query_string: str) -> list[int]:
    return [int(param) for param in query_string.split(",")]
