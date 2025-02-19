from datetime import datetime

from django.db.models import Count, F
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
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()

    @staticmethod
    def _str_id_in_int(query_string) -> list:
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = MovieListSerializer

        if self.action == "retrieve":
            serializer = MovieDetailSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = self._str_id_in_int(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = self._str_id_in_int(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = MovieSessionListSerializer

        if self.action == "retrieve":
            serializer = MovieSessionDetailSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset

        date_string = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date_string:
            date_object = datetime.strptime(date_string, "%Y-%m-%d")
            queryset = queryset.filter(show_time__date=date_object)

        if movie_id:
            queryset = queryset.filter(movie__id=movie_id)

        if self.action == "list":
            queryset = (
                queryset.prefetch_related("movie", "cinema_hall")
                .select_related()
                .annotate(
                    tickets_available=(F("cinema_hall__rows")
                                       * F("cinema_hall__seats_in_row")
                                       - Count("tickets"))
                )
            )

        return queryset.order_by("id")


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderListSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
