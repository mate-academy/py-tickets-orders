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
    def _param_to_ints(id_s_string: str) -> list:
        return [int(str_id) for str_id in id_s_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors:
            queryset = queryset.filter(actors__in=self._param_to_ints(actors))
        if genres:
            queryset = queryset.filter(genres__in=self._param_to_ints(genres))
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


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
        def _params_to_ids(params):
            return [int(param) for param in params.split(",")]

        seats_in_row = F("cinema_hall__seats_in_row")
        rows = F("cinema_hall__rows")

        cinema_hall_capacity = seats_in_row * rows

        queryset = (
            MovieSession.objects.prefetch_related(
                "movie", "cinema_hall"
            ).annotate(
                tickets_available=(cinema_hall_capacity - Count("tickets"))
            )
        ).order_by("id")

        movie = self.request.query_params.get("movie")
        if movie:
            movie_ids = _params_to_ids(movie)
            queryset = queryset.filter(movie__in=movie_ids)

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__contains=date)

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
