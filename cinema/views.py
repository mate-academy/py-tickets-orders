import datetime

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
    queryset = Movie.objects.all().prefetch_related("actors", "genres")
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)
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
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
        movie = self.request.query_params.get("movie")
        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(F("cinema_hall__rows")
                                       * F("cinema_hall__seats_in_row")
                                       - Count("tickets")
                                       )
                )
            )

            date_str = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            if date_str:
                try:
                    date = datetime.datetime.strptime(
                        date_str,
                        "%Y-%m-%d"
                    ).date()
                    queryset = queryset.filter(show_time__date=date)
                except ValueError:
                    pass
        if movie:
            movies_ids = [int(str_id) for str_id in movie.split(",")]
            queryset = queryset.filter(movie__id__in=movies_ids)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


# new

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related(
            "tickets",
            "tickets__movie_session",
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
