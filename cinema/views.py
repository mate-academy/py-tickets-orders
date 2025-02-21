from django.db.models import Count, F
from rest_framework import viewsets

from cinema.functions import (
    _filter_by_actor_id,
    _filter_by_genre_id,
    _filter_by_movie_title,
    _filter_by_date,
    _filter_by_movie_id,
)
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    OrderListSerializer,
    MovieSessionAdvancedListSerializer,
)
from cinema_service.pagination import OrderPagination


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

    def get_queryset(self):
        queryset = Movie.objects.all().prefetch_related("actors", "genres")

        actors = self.request.GET.get("actors")
        genres = self.request.GET.get("genres")
        movie_title = self.request.GET.get("title")

        if actors:
            queryset = _filter_by_actor_id(queryset, actors)

        if genres:
            queryset = _filter_by_genre_id(queryset, genres)

        if movie_title:
            queryset = _filter_by_movie_title(queryset, movie_title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionAdvancedListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.all().prefetch_related(
            "movie",
            "cinema_hall"
        )

        date = self.request.GET.get("date")
        movies = self.request.GET.get("movie")

        if self.action == "list":
            queryset = (
                queryset
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets"))
                )
            )

        if date:
            queryset = _filter_by_date(queryset, date)
        if movies:
            queryset = _filter_by_movie_id(queryset, movies)

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return (
            self.queryset.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderSerializer
        else:
            return OrderSerializer
