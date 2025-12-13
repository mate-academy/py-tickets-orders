from django.db.models import F
from django.db.models.aggregates import Count
from rest_framework import viewsets, pagination
from rest_framework.exceptions import ValidationError

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
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects
    serializer_class = GenreSerializer

    def get_queryset(self):
        genres = self.request.query_params.get("genres")
        if genres:
            genres = genres.split(",")
            if all(obj.isdigit() for obj in genres):
                return self.queryset.filter(id__in=map(int, genres))
            else:
                return self.queryset.none()
        return self.queryset.all()


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects
    serializer_class = ActorSerializer

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        if actors:
            actors = actors.split(",")
            if all(obj.isdigit() for obj in actors):
                return self.queryset.filter(id__in=map(int, actors))
            else:
                return self.queryset.none()
        return self.queryset.all()


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors = map(int, actors.split(","))
            self.queryset = self.queryset.filter(
                actors__in=actors,
            )

        if genres:
            genres = map(int, genres.split(","))
            self.queryset = self.queryset.filter(
                genres__in=genres,
            )
        if title:
            self.queryset = self.queryset.filter(
                title__icontains=title,
            )
        return self.queryset.all()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date:
            self.queryset = self.queryset.filter(
                show_time__date=date,
            )
        if movie_id:
            self.queryset = self.queryset.filter(
                movie_id=movie_id,
            )
        return self.queryset.annotate(
            tickets_available=F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
            - Count("tickets")
        )


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects
    serializer_class = OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related(
            "tickets",
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
