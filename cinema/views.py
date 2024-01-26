from datetime import datetime

from django.db.models import F, Count
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
    MovieListSerializer, OrderSerializer, OrderCreateSerializer,
)


class OrderPaginator(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page"
    max_page_size = 100


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
    def strtolist(string):
        return string.split(",")

    def get_queryset(self):
        queryset = self.queryset
        if self.request.query_params:
            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            title = self.request.query_params.get("title")
            if actors:
                actors = self.strtolist(actors)
                queryset = queryset.filter(actors__in=actors)
            if genres:
                genres = self.strtolist(genres)
                queryset = queryset.filter(genres__in=genres)
            if title:
                queryset = queryset.filter(title__icontains=title)
        return queryset


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
        queryset = self.queryset
        if self.request.query_params:
            movie = self.request.query_params.get("movie")
            date = self.request.query_params.get("date")
            if movie:
                queryset = queryset.filter(movie_id=movie)
            if date:
                date = datetime.strptime(date, "%Y-%m-%d")
                queryset = queryset.filter(
                    show_time__date=date)
        queryset = queryset.select_related("movie").annotate(
            tickets_available=(F("cinema_hall__rows")
                               * F("cinema_hall__seats_in_row")
                               - Count("tickets")))
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPaginator

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user.id)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
