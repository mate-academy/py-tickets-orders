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
    MovieListSerializer,
    OrderSerializer,
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    @staticmethod
    def str_list_to_int_list(str_list):
        int_list = [int(str_id) for str_id in str_list.split(",")]
        return int_list

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = self.str_list_to_int_list(actors)
            queryset = queryset.filter(actors__in=actors_ids)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = MovieViewSet.str_list_to_int_list(genres)
            queryset = queryset.filter(genres__in=genres_ids)
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

    def get_queryset(self):
        queryset = self.queryset

        date_str = self.request.query_params.get("date")
        if date_str:
            _date = datetime.strptime(date_str, "%Y-%m-%d")
            queryset = queryset.filter(show_time__date=_date)
            # queryset = queryset.filter(show_time=date_str)

        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie=movie)

        if self.action == "list":
            queryset = queryset.select_related(
                "cinema_hall", "movie"
            ).prefetch_related("tickets")
        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 2

    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie",
        )

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderListSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
