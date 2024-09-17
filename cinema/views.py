from datetime import datetime

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
    MovieListSerializer, OrderSerializer, OrderListSerializer,
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

    def from_int_to_dict(self, query_string):
        return [int(actors_id) for actors_id in query_string.split(",")]

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        movies = Movie.objects.all()
        if actors:
            actors = self.from_int_to_dict(actors)
            movies = movies.filter(actors__id__in=actors)

        if genres:
            genres = self.from_int_to_dict(genres)
            movies = movies.filter(genres__id__in=genres)

        if title:
            movies = movies.filter(title__icontains=title)

        movies = movies.prefetch_related("genres")
        movies = movies.prefetch_related("actors")

        return movies


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def from_int_to_dict(self, query_string):
        return [int(actors_id) for actors_id in query_string.split(",")]

    def get_queryset(self):
        movie_sessions = MovieSession.objects.all()
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie:
            movie = self.from_int_to_dict(movie)
            movie_sessions = movie_sessions.filter(movie__id__in=movie)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
            movie_sessions = movie_sessions.filter(show_time__date=date)

        movie_sessions = movie_sessions.select_related("movie")
        movie_sessions = movie_sessions.select_related("cinema_hall")

        return movie_sessions


class OrderPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrive":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
