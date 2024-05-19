from datetime import datetime

from django.db.models import F
from rest_framework import viewsets, generics
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


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__in=actors_ids)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__in=genres_ids)
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

    def get_queryset(self):
        queryset = self.queryset

        _date = self.request.query_params.get("date")
        if _date:
            year, month, day = (int(_) for _ in _date.split("-"))
            queryset = queryset.filter(
                show_time__year=year,
                show_time__month=month,
                show_time__day=day
            )

        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie=movie)

        if self.action == "list":
            queryset = (queryset.select_related(
                "cinema_hall", "movie"
            ).prefetch_related("tickets")
            )
        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 2

    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie"
        )

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
