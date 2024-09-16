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


class ParamsToIntMixin:
    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(ParamsToIntMixin, viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("actors", "genres")
        genre = self.request.query_params.get("genres", None)
        actor = self.request.query_params.get("actors", None)
        title = self.request.query_params.get("title", None)

        if genre:
            genres = self._params_to_ints(genre)
            queryset = queryset.filter(genres__in=genres)
        if actor:
            actors = self._params_to_ints(actor)
            queryset = queryset.filter(actors__in=actors)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(ParamsToIntMixin, viewsets.ModelViewSet):
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
        date = self.request.query_params.get("date", None)
        movie = self.request.query_params.get("movie", None)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(show_time__date=date)
        if movie:
            movies = self._params_to_ints(movie)
            queryset = queryset.filter(movie__in=movies)
        if self.action == "list":
            queryset = queryset.select_related().annotate(
                tickets_available=F("cinema_hall__rows"
                                    ) * F("cinema_hall__seats_in_row"
                                          ) - Count("tickets"))
            return queryset.select_related()
        if self.action == "retrieve":
            return queryset.select_related()

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            return OrderListSerializer
        return serializer
