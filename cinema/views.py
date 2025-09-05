from typing import Type

from django.db.models import F, Count, QuerySet
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import Serializer

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    GenreSerializer,
    MovieSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListAvailableSerializer,
    MovieSessionSerializer,
    OrderListSerializer,
    OrderSerializer,
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
    def _parse_ids_from_string(query_string: str) -> list[int]:
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if actors := self.request.query_params.get("actors"):
            actor_ids = self._parse_ids_from_string(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)

        if genres := self.request.query_params.get("genres"):
            genre_ids = self._parse_ids_from_string(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)

        if title := self.request.query_params.get("title"):
            queryset = queryset.filter(title__icontains=title)

        if self.action == "list":
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset.distinct()

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if date := self.request.query_params.get("date"):
            queryset = queryset.filter(show_time__date=date)

        if movie := self.request.query_params.get("movie"):
            movie_ids = [int(str_id) for str_id in movie.split(",")]
            queryset = queryset.filter(movie__id__in=movie_ids)

        if self.action == "list":
            queryset = (
                queryset.select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    )
                    - Count("tickets")
                )
            )

        return queryset.distinct()

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieSessionListAvailableSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self) -> QuerySet:
        queryset = Order.objects.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )
        return queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action in ("list", "retrieve"):
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(user=self.request.user)
