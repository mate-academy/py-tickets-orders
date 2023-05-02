from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (Genre,
                           Actor,
                           CinemaHall,
                           Movie,
                           MovieSession,
                           Order)

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


def make_int_list(string) -> list[int]:
    return [int(num) for num in string.split(",")]


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

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_id = make_int_list(actors)
            queryset = queryset.filter(actors__id__in=actors_id)
        if genres:
            genres_id = make_int_list(genres)
            queryset = queryset.filter(genres__id__in=genres_id)
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

    def get_queryset(self):
        queryset = self.queryset

        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            movie_id = make_int_list(movie)
            queryset = queryset.filter(movie__id__in=movie_id)
        if self.action == "list":
            queryset = (
                queryset.select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=F("cinema_hall__rows")
                                      * F("cinema_hall__seats_in_row") - Count("tickets")
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return self.serializer_class


class OrderListPagination(PageNumberPagination):
    page_size = 1
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderListPagination
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    def get_queryset(self):
        return Order.objects.prefetch_related(
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie",
        ).filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
