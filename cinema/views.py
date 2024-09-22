from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.filters import FilterMovieSessionByDateAndMovie, FilterMovieViewSet
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
    filter_backends = [FilterMovieViewSet]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        return self.queryset.prefetch_related("genres", "actors")


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    filter_backends = [FilterMovieSessionByDateAndMovie]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .prefetch_related("tickets")
                .annotate(
                    tickets_available=(F("cinema_hall__rows") * F(
                        "cinema_hall__seats_in_row")) - Count("tickets")
                ).order_by("id")
            )

        return queryset


class OrderResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 1


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderResultsSetPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        query_set = self.queryset.select_related(
            "user"
        ).prefetch_related(
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie"
        )

        if self.action == "list":
            query_set = query_set.filter(user=self.request.user)

        return query_set

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderListSerializer

        return serializer
