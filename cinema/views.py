from rest_framework import viewsets
from django.db.models import Count, F

from cinema.pagination import OrderSetPagination
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
    OrderSerializer,
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

    def get_queryset(self):
        queryset = self.queryset
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")
        if genres:
            genres = params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genres)

        if actors:
            actors = params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actors)

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
        queryset = self.queryset.select_related()
        if self.action == "list":

            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            if date:
                queryset = queryset.filter(show_time__date=date)
                print(queryset)

            if movie:
                movie = params_to_int(movie)
                queryset = queryset.filter(movie__id__in=movie)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def params_to_int(query_string) -> list[int]:
    return [int(id) for id in query_string.split(",")]
