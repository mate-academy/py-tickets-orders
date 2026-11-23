from django.db.models import Count, F, QuerySet
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from cinema.models import Actor, CinemaHall, Genre, Movie, MovieSession, Order
from cinema.pagination import OrderPagination
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSerializer,
    MovieSessionAvailabilitySerializer,
    MovieSessionDetailSerializer,
    MovieSessionSerializer,
    OrderListSerializer,
    OrderSerializer,
)


def params_to_ints(query_string: str) -> list[int]:
    return [int(str_id) for str_id in query_string.split(",")]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            queryset = queryset.filter(genres__id__in=params_to_ints(genres))
        if actors:
            queryset = queryset.filter(actors__id__in=params_to_ints(actors))
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if self.action == "list":
            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            if date:
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.filter(movie_id=int(movie))
            queryset = queryset.select_related(
                "movie", "cinema_hall"
            ).annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )

        if self.action == "retrieve":
            queryset = queryset.select_related(
                "movie", "cinema_hall"
            ).prefetch_related("movie__genres", "movie__actors", "tickets")

        return queryset

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "list":
            return MovieSessionAvailabilitySerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )

        return queryset

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer: OrderSerializer) -> None:
        serializer.save(user=self.request.user)
