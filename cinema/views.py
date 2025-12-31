from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets, pagination

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


def _get_ids_from_q_param(q_param):
    return [int(str_id) for str_id in q_param.split(",")]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related(
        "genres",
        "actors"
    )
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors:
            actors_ids = _get_ids_from_q_param(actors)
            queryset = queryset.filter(
                actors__id__in=actors_ids
            )

        if genres:
            genres_ids = _get_ids_from_q_param(genres)
            queryset = queryset.filter(
                genres__id__in=genres_ids
            )

        if title:
            queryset = queryset.filter(
                title__icontains=title
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = (MovieSession.objects
                .select_related(
                    "movie",
                    "cinema_hall",
                )
                .prefetch_related(
                    "tickets"
                ))
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        format_string = "%Y-%m-%d"
        date_filter_data = self.request.query_params.get("date")
        movies_ids = self.request.query_params.get("movie")

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )
            if date_filter_data:
                date_filter_data = datetime.strptime(
                    self.request.query_params.get("date"),
                    format_string
                )
                queryset = queryset.filter(
                    show_time__date=date_filter_data
                )
            if movies_ids:
                movies_ids = _get_ids_from_q_param(
                    self.request.query_params.get("movie")
                )
                queryset = queryset.filter(movie__id__in=movies_ids)

        return queryset


class OrderPagination(pagination.PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (Order.objects
                .select_related("user")
                .prefetch_related(
                    "tickets",
                    "tickets__movie_session",
                    "tickets__movie_session__movie",
                    "tickets__movie_session__cinema_hall",
                ))

    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            return OrderListSerializer

        return serializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
