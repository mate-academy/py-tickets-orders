from rest_framework import viewsets
from datetime import datetime, timedelta

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
    MovieListSerializer,
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

    def get_queryset(self):
        qs = self.queryset
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            genres = genres.split(",")
            qs = qs.filter(genres__id__in=genres)
        if actors:
            actors = actors.split(",")
            qs = qs.filter(actors__id__in=actors)
        if title:
            qs = qs.filter(title__icontains=title)

        return qs


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "cinema_hall", "movie"
    ).prefetch_related("movie__genres", "movie__actors")
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        qs = self.queryset
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie:
            qs = qs.filter(movie=movie)
        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(days=1)

            qs = qs.filter(show_time__gte=start, show_time__lt=end)

        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self):
        if self.action == "list" and self.request.user.is_authenticated:
            user = self.request.user
            return self.queryset.filter(user=user)
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderListSerializer
