from datetime import datetime

from django.db.models import F
from django.db.models.aggregates import Count
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
    OrderListSerializer,
    OrderCreateSerializer,
)


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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            queryset = queryset.filter(
                actors__id__in=list(map(int, actors.split(",")))
            )
        if genres:
            queryset = queryset.filter(
                genres__id__in=list(map(int, genres.split(",")))
            )
        if title:
            queryset = queryset.filter(
                title__icontains=title
            )
        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.select_related(
                "cinema_hall", "movie"
            ).prefetch_related(
                "tickets"
            ).annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if movie:
            queryset = queryset.filter(movie__id=int(movie))
        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(
                show_time__date=date
            )
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.filter(
                user=self.request.user
            ).prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        return queryset

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = OrderListSerializer
        elif self.action == "create":
            serializer = OrderCreateSerializer
        return serializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
