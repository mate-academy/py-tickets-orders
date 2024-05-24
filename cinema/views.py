from datetime import datetime
from typing import Type

from django.db.models import (
    QuerySet,
    Count,
    F,
    ExpressionWrapper,
    IntegerField
)
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
    OrderListSerializer
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
    def _split_query_params(ids: str):
        return [int(str_id) for str_id in ids.split(",")]

    def get_queryset(self) -> QuerySet[Movie]:
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors = self._split_query_params(actors)
            queryset = queryset.filter(actors__id__in=actors)

        if genres:
            genres = self._split_query_params(genres)
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

    @staticmethod
    def _split_query_params(ids: str):
        return [int(str_id) for str_id in ids.split(",")]

    def get_queryset(self) -> QuerySet[MovieSession]:
        queryset = self.queryset.select_related("cinema_hall", "movie")

        if self.action == "list":
            queryset = (
                queryset
                .annotate(
                    cinema_hall_capacity=ExpressionWrapper(
                        F(
                            "cinema_hall__rows"
                        ) * F(
                            "cinema_hall__seats_in_row"
                        ),
                        output_field=IntegerField()
                    ),
                    tickets_available=ExpressionWrapper(
                        F("cinema_hall_capacity") - Count("tickets"),
                        output_field=IntegerField()
                    )
                )
            )

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            print("filtering by: ", date)
            queryset = queryset.filter(
                show_time__date=datetime.strptime(
                    date,
                    "%Y-%m-%d"
                )
                .date()
            )

        if movie:
            movie = self._split_query_params(movie)
            queryset = queryset.filter(movie_id__in=movie)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet[Order]:
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )

        return queryset

    def perform_create(self, serializer: OrderSerializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> Type[
        OrderListSerializer | OrderSerializer
    ]:
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderListSerializer

        return serializer
