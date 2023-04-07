from datetime import datetime
from typing import Type

from django.db.models import F, Count, QuerySet
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import Serializer

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
    OrderListSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


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
    serializer_class = MovieSerializer
    queryset = Movie.objects.prefetch_related("actors", "genres")

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        if actors:
            actors = [int(actor) for actor in actors.split(",")]
            queryset = queryset.filter(actors__in=actors)

        genres = self.request.query_params.get("genres")
        if genres:
            genres = [int(genre) for genre in genres.split(",")]
            queryset = queryset.filter(genres__in=genres)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "cinema_hall",
        "movie"
    ).prefetch_related(
        "tickets",
    )
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=F(
                    "cinema_hall__seats_in_row"
                ) * F("cinema_hall__rows") - Count("tickets")
            )

        date = self.request.query_params.get("date")
        if date:
            format_string = "%Y-%m-%d"
            date = datetime.strptime(date, format_string)
            queryset = queryset.filter(show_time__date=date.date())

        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie=movie)

        return queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets__movie_session")
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if self.action == "list":
            return queryset.filter(user=self.request.user)
        return self.queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "post":
            return OrderSerializer
        return OrderListSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
