from datetime import datetime
from typing import Type

from django.db.models import QuerySet, F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import Serializer

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieListSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
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


class ParamToIntsBaseClass:
    @staticmethod
    def _params_to_ints(params: str) -> list[int]:
        return [int(item) for item in params.split(",")]


class MovieViewSet(viewsets.ModelViewSet, ParamToIntsBaseClass):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        filters = self.request.query_params
        if filters:
            if filters.get("genres"):
                queryset = queryset.filter(
                    genres__in=self._params_to_ints(filters.get("genres"))
                )
            if filters.get("actors"):
                queryset = queryset.filter(
                    actors__in=self._params_to_ints(filters.get("actors"))
                )
            if filters.get("title"):
                queryset = queryset.filter(
                    title__icontains=filters.get("title")
                )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet, ParamToIntsBaseClass):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.prefetch_related("tickets")
        filters = self.request.query_params

        if filters:
            if filters.get("date"):
                date_obj = datetime.strptime(
                    filters.get("date"),
                    "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(show_time__date=date_obj)
            if filters.get("movie"):
                queryset = queryset.filter(
                    movie_id__in=self._params_to_ints(filters.get("movie"))
                )

        if self.action == "list":
            queryset = queryset.select_related("cinema_hall").annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                )
                - Count("tickets")
            )

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
            return queryset
        return queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
