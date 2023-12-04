import datetime

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

    @staticmethod
    def _params_to_ints(params: str) -> list:
        return [int(param) for param in params.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        actors_filter_data = self.request.query_params.get("actors")
        if actors_filter_data:
            actors_filter_list = self._params_to_ints(actors_filter_data)
            queryset = queryset.filter(actors__id__in=actors_filter_list)
        genres_filter_data = self.request.query_params.get("genres")
        if genres_filter_data:
            genres_filter_list = self._params_to_ints(genres_filter_data)
            queryset = queryset.filter(genres__id__in=genres_filter_list)
        title_filter = self.request.query_params.get("title")
        if title_filter:
            queryset = queryset.filter(title__contains=title_filter)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.select_related("cinema_hall").annotate(
                tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )
        date_filter = self.request.query_params.get("date")
        if date_filter:
            date_list = [int(param) for param in date_filter.split("-")]
            date = datetime.date(*date_list)
            queryset = queryset.filter(show_time__date=date)
        movie_filter = self.request.query_params.get("movie")
        if movie_filter:
            movie_id = int(movie_filter)
            queryset = queryset.filter(movie__id=movie_id)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
