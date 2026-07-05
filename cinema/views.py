from django.db.models import Count, F
from rest_framework import viewsets

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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def _parse_genres_actors_param(param):
        return [int(item.strip()) for item in param.split(",")
                if item.strip().isdigit()]

    def get_queryset(self):
        qs = self.queryset
        genres_filter = self.request.query_params.get("genres")
        actors_filter = self.request.query_params.get("actors")
        title_filer = self.request.query_params.get("title")
        if genres_filter:
            qs = qs.filter(
                genres__in=self._parse_genres_actors_param(genres_filter))
        if actors_filter:
            qs = qs.filter(
                actors__in=self._parse_genres_actors_param(actors_filter))
        if title_filer:
            qs = qs.filter(title__icontains=title_filer.strip())
        return qs


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
        qs = self.queryset
        date_filter = self.request.query_params.get("date")
        movie_filter = self.request.query_params.get("movie")

        if date_filter:
            qs = qs.filter(show_time__date=date_filter)

        if movie_filter:
            qs = qs.filter(movie__id=movie_filter.strip())

        if self.action == "list":
            qs = qs.select_related("cinema_hall")
            return qs.annotate(
                available=F("cinema_hall__rows") * F(
                    "cinema_hall__seats_in_row") - Count("tickets")
            )

        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = Order.objects.filter(user=self.request.user)
        if self.action == "list":
            qs = qs.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class
