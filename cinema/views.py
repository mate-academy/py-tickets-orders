from datetime import datetime

from django.db.models import Count, F, ExpressionWrapper, IntegerField
from django.utils.dateparse import parse_date
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

    def get_queryset(self):
        queryset = super().get_queryset()

        actors = self.request.query_params.getlist("actors")
        if len(actors) == 1 and "," in actors[0]:
            actors = actors[0].split(",")
        if actors:
            try:
                actors = [int(actor_id) for actor_id in actors]
                queryset = queryset.filter(actors__id__in=actors)
            except ValueError:
                pass  # або можна кинути помилку, якщо це критично

        genres = self.request.query_params.getlist("genres")
        if len(genres) == 1 and "," in genres[0]:
            genres = genres[0].split(",")
        if genres:
            try:
                genres = [int(genre_id) for genre_id in genres]
                queryset = queryset.filter(genres__id__in=genres)
            except ValueError:
                pass

        return queryset.distinct()
    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        elif self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        movie_id = self.request.query_params.get("movie")
        date_str = self.request.query_params.get("date")

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    parts = list(map(int, date_str.split("-")))
                    if len(parts) == 3:
                        date = datetime(parts[0], parts[1], parts[2]).date()
                    else:
                        date = None
                except Exception:
                    date = None

            if date:
                queryset = queryset.filter(
                    show_time__year=date.year,
                    show_time__month=date.month,
                    show_time__day=date.day,
                )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
