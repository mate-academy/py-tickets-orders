from typing import Type
from django.db.models import QuerySet, F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def params_to_ints(params) -> list:
        return [int(str_id) for str_id in params.split(",")]

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if genres:
            genres_ids = self.params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if actors:
            actors_ids = self.params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action == "list":
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie:
            queryset = queryset.filter(movie__id=int(movie))

        if self.action == "list":
            queryset = queryset.select_related("movie", "cinema_hall")

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(user_id=self.request.user.id)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )

        return queryset

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> Type:
        if self.action == "list":
            return OrderListSerializer

        return self.serializer_class
