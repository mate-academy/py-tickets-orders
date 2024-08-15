from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

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
    MovieListSerializer, OrderSerializer, TicketSerializer,
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


class MoviesViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    queryset = Movie.objects.prefetch_related("genres", "actors")

    def get_queryset(self):
        queryset = super().get_queryset()
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")
        if genres:
            genre_ids = genres.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids).distinct()
        if actors:
            actor_ids = actors.split(",")
            queryset = queryset.filter(actors__id__in=actor_ids).distinct()
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return self.serializer_class


class MoviesSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.all()
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date)

            except ValueError:
                raise ValueError("The date should be provided in year-month-day format")
        if movie:
            movie_ids = [int(movie_id) for movie_id in movie.split(",")]
            queryset = queryset.filter(movie__id__in=movie_ids)
        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie")
                .annotate(tickets_available=F("cinema_hall__rows") * F("cinema_hall__seats_in_row") - Count("tickets"))
            ).order_by("id")
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.all()
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
