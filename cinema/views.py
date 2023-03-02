from typing import Type

from django.db.models import QuerySet, F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import Serializer

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
    OrderListSerializer,
)


def params_to_ints(qs: str) -> list[int]:
    """Converts a list of string IDs to a list of integers"""
    return [int(str_id) for str_id in qs.split(",")]


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
    queryset = Movie.objects.prefetch_related("genres", "actors")

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        if title is not None:
            queryset = queryset.filter(
                title__icontains=title
            )

        if actors is not None:
            actors_ids = params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres is not None:
            genres_ids = params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        return queryset.distinct()

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if self.action == "list":
            all_seats = F("cinema_hall__seats_in_row") * F("cinema_hall__rows")
            queryset = queryset.annotate(
                tickets_available=(
                    all_seats - Count("tickets")
                )
            )

        all_params = {
            "movie": self.request.query_params.get("movie"),
            "date": self.request.query_params.get("date"),
        }

        if all_params["date"] is not None:
            queryset = queryset.filter(
                show_time__date=all_params["date"]
            )

        if all_params["movie"] is not None:
            movie_ids = params_to_ints(all_params["movie"])
            queryset = queryset.filter(movie__id__in=movie_ids)

        return queryset.distinct()

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")

        return queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(user=self.request.user)
