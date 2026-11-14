from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import OrderPagination

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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors_filter = self.request.query_params.get("actors")
        genres_filter = self.request.query_params.get("genres")
        title_filter = self.request.query_params.get("title")

        if actors_filter:
            queryset = queryset.filter(
                actors__in=self._parse_field_param(actors_filter)
            ).distinct()

        if genres_filter:
            queryset = queryset.filter(
                genres__in=self._parse_field_param(genres_filter)
            ).distinct()

        if title_filter:
            queryset = queryset.filter(
                title__icontains=title_filter
            ).distinct()

        if self.action in ["list", "retrieve"]:
            return queryset.prefetch_related("actors")
        else:
            return queryset.all()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def _parse_field_param(param):
        return [
            int(field.strip())
            for field in param.split(",")
            if field.strip().isdigit()
        ]


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        show_time_filter = self.request.query_params.get("date")
        movie_filter = self.request.query_params.get("movie")

        if show_time_filter:
            queryset = queryset.filter(
                show_time__date=show_time_filter
            ).distinct()

        if movie_filter:
            queryset = queryset.filter(
                movie__in=self._parse_field_param(movie_filter)
            ).distinct()

        return queryset.all()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    @staticmethod
    def _parse_field_param(param):
        return [
            int(field.strip())
            for field in param.split(",")
            if field.strip().isdigit()
        ]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class
