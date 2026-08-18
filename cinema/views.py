from django.db.models import Q, F, Count
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import BasePagination

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


def params_to_integer_list(params: str) -> list[int]:
    return [int(param_id) for param_id in params.split(",")]


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
        elif self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        query_filter = Q()
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors = params_to_integer_list(actors)
            query_filter &= Q(actors__in=actors)

        if genres:
            genres = params_to_integer_list(genres)
            query_filter &= Q(genres__in=genres)

        if title:
            query_filter &= Q(title__icontains=title)

        return Movie.objects.filter(query_filter).distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        query_filter = Q()
        query_set = MovieSession.objects.all()

        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if self.action == "list":
            query_set = query_set.select_related(
                "movie", "cinema_hall"
            ).annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )

        if movie:
            movie = params_to_integer_list(movie)
            query_filter &= Q(movie__in=movie)

        if date:
            query_filter &= Q(show_time__date=date)

        return query_set.filter(query_filter).distinct()


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = BasePagination

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
