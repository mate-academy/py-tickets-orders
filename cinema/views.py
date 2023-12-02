from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_ints(parameter: str):
        return [int(value) for value in parameter.split(",")]

    def get_queryset(self):
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            genres_ids = self._params_to_ints(genres)
            self.queryset = self.queryset.filter(
                genres__id__in=genres_ids
            ).distinct()
        if actors:
            actors_ids = self._params_to_ints(actors)
            self.queryset = self.queryset.filter(
                actors__id__in=actors_ids
            ).distinct()
        if title:
            self.queryset = self.queryset.filter(
                title__icontains=title
            )

        return self.queryset.prefetch_related("genres", "actors")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    @staticmethod
    def _params_to_ints(parameter: str):
        return [int(value) for value in parameter.split(",")]

    def get_queryset(self):
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            self.queryset = self.queryset.filter(
                show_time__date=date
            )
        if movie:
            movie_ids = self._params_to_ints(movie)
            self.queryset = self.queryset.filter(
                movie_id__in=movie_ids
            ).distinct()

        self.queryset = self.queryset.prefetch_related(
            "tickets", "cinema_hall", "movie"
        ).annotate(tickets_available=(
            F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row")
            - Count("tickets")
        ), )
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.filter(
                user_id=self.request.user.id
            ).prefetch_related("tickets")
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
