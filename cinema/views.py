from django.db import transaction, IntegrityError
from rest_framework import viewsets, serializers


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
    OrderUpdateSerializer,
)

from cinema.paginations import OrderListPagination
from cinema.utils import query_param_value_to_split


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

        actors = query_param_value_to_split(
            "actors",
            self.request.query_params
        )

        genres = query_param_value_to_split(
            "genres",
            self.request.query_params

        )
        title: list = self.request.query_params.get(
            "title",
            None
        )

        if actors:
            queryset = queryset.filter(actors__id__in=actors)

        if genres:
            queryset = queryset.filter(genres__id__in=genres)

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
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        date_str = self.request.query_params.get("date", None)
        movie = query_param_value_to_split(
            "movie",
            self.request.query_params
        )

        if date_str:
            queryset = queryset.filter(show_time__date=date_str)

        if movie:
            queryset = queryset.filter(movie__id__in=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session",
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderListPagination

    def get_queryset(self):
        queryset = self.queryset
        return queryset.filter(user__id=self.request.user.id)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list" or self.action == "retrieve":
            serializer = OrderListSerializer
        if self.action == "update":
            serializer = OrderUpdateSerializer

        return serializer

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                return serializer.save(user_id=self.request.user.id)
        except IntegrityError:
            raise serializers.ValidationError({
                "order": "Something went wrong."
            })
