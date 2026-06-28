from django.db.models import F, Count
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
    MovieListSerializer, OrderSerializer, OrderListSerializer,
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

    def get_queryset(self):
        queryset = self.queryset

        actors_filter = self.request.query_params.get("actors")
        if actors_filter:
            queryset = queryset.filter(
                actors__in=self._parse_actors_param(actors_filter)
            )
        genres_filter = self.request.query_params.get("genres")
        if genres_filter:
            queryset = queryset.filter(
                genres__in=self._parse_genres_param(genres_filter)
            )
        title_filter = self.request.query_params.get("title")
        if title_filter:
            queryset = queryset.filter(title__icontains=title_filter)
        return queryset.all()

    @staticmethod
    def _parse_actors_param(params):
        return [
            int(actors.strip())
            for actors in params.split(",")
            if actors.strip().isdigit()
        ]

    @staticmethod
    def _parse_genres_param(params):
        return [
            int(genres.strip())
            for genres in params.split(",")
            if genres.strip().isdigit()
        ]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset

        date_filter = self.request.query_params.get("date")
        if date_filter:
            queryset = queryset.filter(show_time__date=date_filter)
        movie_filter = self.request.query_params.get("movie")
        if movie_filter:
            queryset = queryset.filter(movie_id=movie_filter)

        if self.action == "list":
            queryset = queryset.select_related().annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        elif self.action == "retrieve":
            return queryset.select_related()
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
