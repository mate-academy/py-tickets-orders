import datetime
from django.db.models import QuerySet, F, Count
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
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
    OrderListSerializer
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
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def _params_to_strings(string_list: str) -> list:
        return [str_param for str_param in string_list.split(",")]

    def get_queryset(self):
        queryset = Movie.objects.all().prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            queryset = queryset.filter(
                actors__in=self._params_to_strings(actors)
            )

        if genres:
            queryset = queryset.filter(
                genres__in=self._params_to_strings(genres)
            )

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.all().select_related(
            "movie", "cinema_hall"
        )

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets")

        movie = self.request.query_params.get("movie")
        show_time = self.request.query_params.get("date")

        if movie:
            try:
                movie = int(movie)
                queryset = queryset.filter(movie=movie)
            except ValueError:
                raise ValidationError(f"{movie} is not correct movie id.")

        if show_time:
            try:
                show_time = datetime.datetime.strptime(
                    show_time, "%Y-%m-%d"
                ).date()
                start_datetime = datetime.datetime.combine(
                    show_time, datetime.datetime.min.time()
                )
                end_datetime = datetime.datetime.combine(
                    show_time, datetime.datetime.max.time()
                )
                queryset = queryset.filter(
                    show_time__range=(start_datetime, end_datetime)
                )
            except ValueError:
                raise ValidationError(f"{show_time} is not correct date.")
        return queryset


class OrderResultsPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    pagination_class = OrderResultsPagination

    def get_queryset(self) -> QuerySet:
        self.queryset = Order.objects.all().filter(user=self.request.user)
        if self.action == "list":
            return self.queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            ).select_related()

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
