from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession, Order
)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, OrderListSerializer, OrderCreateSerializer
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
    def _params_to_int(string):
        return [int(params) for params in string.split(",")]

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = self._params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = self._params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    @staticmethod
    def _params_to_int(string):
        return [int(params) for params in string.split(",")]

    def get_queryset(self):
        queryset = self.queryset.select_related("cinema_hall", "movie")

        if self.action == "list":
            queryset = (
                queryset
                .annotate(tickets_available=F("cinema_hall__seats_in_row") * F(
                    "cinema_hall__rows") - Count("tickets"))
            )

        movies = self.request.query_params.get("movie")
        if movies:
            movies_ids = self._params_to_int(movies)
            queryset = queryset.filter(movie__id__in=movies_ids)

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset \
                .filter(show_time=datetime.strptime(date, "%Y-%m-%d"))

        return queryset.distinct()


class OrderPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size'
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer

        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )

        if self.action == "retrieve":
            return queryset.prefetch_related("tickets")

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
