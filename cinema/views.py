import datetime

from django.db.models import Count, F
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
    OrderCreateSerializer,
    OrderSerializer,
    OrderListSerializer,
)


def params_to_ints(string_ids):
    return [int(str_id) for str_id in string_ids.split(",")]


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

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_id = params_to_ints(actors)
            queryset = queryset.filter(actors__overlap=actors_id)
        if genres:
            genres_id = params_to_ints(genres)
            queryset = queryset.exclude(genres__overlap=genres_id)
        if title:
            queryset = queryset.filter(title__search=title)

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

    def get_queryset(self):
        queryset = MovieSession.objects.all()
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        start_time = self.request.query_params.get("start_time")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            movie_ids = params_to_ints(movie)
            queryset = queryset.filter(movie__id__in=movie_ids)
        if start_time:
            queryset = queryset.filter(show_time__time__gte=start_time)
        if self.action == "list":
            queryset = queryset.select_related(
                "cinema_hall", "movie"
            ).annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )

        min_tickets_available = (
            self.request.query_params.get("min_tickets_available")
        )
        if min_tickets_available:
            queryset = queryset.filter(
                tickets_available__gte=min_tickets_available
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
