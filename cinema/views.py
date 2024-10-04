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

    @staticmethod
    def _make_int_from_str(query):
        return [int(num) for num in query.split(",")]

    def get_queryset(self):
        query_set = self.queryset
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            query_set = query_set.filter(title__icontains=title)

        if genres:
            genres_ids = self._make_int_from_str(genres)
            query_set = query_set.filter(genres__id__in=genres_ids)

        if actors:
            actors_ids = self._make_int_from_str(actors)
            query_set = query_set.filter(actors__id__in=actors_ids)

        return query_set.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        MovieSession.objects.all()
        .select_related("movie", "cinema_hall")
        .annotate(
            tickets_available=F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row")
            - Count("tickets")
        )
    )
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        query_set = (
            MovieSession.objects.all()
            .select_related("movie", "cinema_hall")
            .annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        )
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if movie:
            movie_ids = int(movie)
            query_set = query_set.filter(movie__id=movie_ids)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            query_set = query_set.filter(show_time__date=date)

        return query_set


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
