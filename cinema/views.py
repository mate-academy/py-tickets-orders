from typing import Type, Any

from django.db.models import QuerySet, Q, F, Count
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import OrderPagination

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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def _transform_params_to_ids(params: str) -> list:
        return [int(str_id) for str_id in params.split(",")]

    def get_filters(self) -> Q:
        filters = Q()

        actors = self.request.query_params.get("actors")
        if actors:
            filters &= Q(actors__in=self._transform_params_to_ids(actors))

        genres = self.request.query_params.get("genres")

        if genres:
            filters &= Q(genres__in=self._transform_params_to_ids(genres))

        title = self.request.query_params.get("title")
        if title:
            filters &= Q(title__icontains=title)
        return filters

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        filters = self.get_filters()

        if filters:
            return queryset.filter(filters)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie")
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_filters(self) -> Q:
        filters = Q()
        date = self.request.query_params.get("date")
        if date:
            filters &= Q(show_time__date=date)

        movie = self.request.query_params.get("movie")
        if movie:
            filters &= Q(movie=movie)

        return filters

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        filters = self.get_filters()
        if filters:
            return queryset.filter(filters)

        if self.action == "list":
            queryset = (
                queryset
                .prefetch_related("cinema_hall", "tickets")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__seats_in_row")
                        * F("cinema_hall__rows")
                        - Count("tickets")
                    )
                )
            )

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related(
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        user_orders = super().get_queryset().filter(user=self.request.user)
        return user_orders

    def get_serializer_class(self) -> Type[OrderCreateSerializer] | Any:
        if self.action == "create":
            return OrderCreateSerializer

        return super().get_serializer_class()
