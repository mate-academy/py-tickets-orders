from typing import Type

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework import pagination
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
    OrderListSerializer,
    OrderCreateSerializer
)


class GenreViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all().prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = MovieSession.objects.all().select_related(
            "movie",
            "cinema_hall"
        )
        if self.action == "list":
            date = self.request.query_params.get("date")
            movies = self.request.query_params.get("movie")

            if date:
                queryset = queryset.filter(show_time__date=date)

            if movies:
                movie_ids = [int(str_id) for str_id in movies.split(",")]
                queryset = queryset.filter(movie__id__in=movie_ids)
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self) -> QuerySet:
        if self.action == "list":
            return Order.objects.filter(
                user=self.request.user
            ).prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        return self.queryset

    def perform_create(self, serializer: Serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> Type[Serializer]:
        serializer_class = OrderListSerializer

        if self.action == "list":
            serializer_class = OrderListSerializer
        elif self.action == "create":
            serializer_class = OrderCreateSerializer
        return serializer_class
