from django.db.models import F
from django.db.models.aggregates import Count
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
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    @staticmethod
    def _params_to_int(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset.prefetch_related(
            "genres", "actors"
        ).distinct()
        genres_query_params = self.request.query_params.get("genres")
        actors_query_params = self.request.query_params.get("actors")
        title_query_params = self.request.query_params.get("title")

        if genres_query_params:
            genres = self._params_to_int(genres_query_params)
            queryset = queryset.filter(genres__id__in=genres)

        if actors_query_params:
            actors = self._params_to_int(actors_query_params)
            queryset = queryset.filter(actors__id__in=actors)

        if title_query_params:
            queryset = queryset.filter(title__icontains=title_query_params)

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
    pagination_class = None

    def get_queryset(self):
        capacity = F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
        queryset = self.queryset
        queryset = (
            queryset
            .select_related("cinema_hall", "movie")
            .annotate(
                tickets_available=(
                    capacity - Count("tickets")
                )
            )
        )
        date_query_params = self.request.query_params.get("date")
        movie_query_params = self.request.query_params.get("movie")
        if date_query_params:
            queryset = queryset.filter(show_time__date=date_query_params)
        if movie_query_params:
            queryset = queryset.filter(movie__id=int(movie_query_params))
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
