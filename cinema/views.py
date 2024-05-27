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
    OrderListSerializer,
    OrderCreateSerializer
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


def _params_to_int(query_string: str):
    return [int(param) for param in query_string.split(",")]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        if actors:
            actors_id = _params_to_int(actors)
            queryset = queryset.filter(actors__in=actors_id)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_id = _params_to_int(genres)
            queryset = queryset.filter(genres__in=genres_id)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        movie = self.request.query_params.get("movie")
        if movie:
            movie_id = int(movie)
            queryset = queryset.filter(movie__id=movie_id)

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(F("cinema_hall__rows")
                                   * F("cinema_hall__seats_in_row")
                                   - Count("tickets"))
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderListPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (Order.objects
                .prefetch_related("tickets__movie_session__cinema_hall")
                .prefetch_related("tickets__movie_session__movie"))
    serializer_class = OrderListSerializer
    pagination_class = OrderListPagination

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.filter(user__id=self.request.user.id)
        return queryset

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.action == "create":
            serializer_class = OrderCreateSerializer
        return serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
