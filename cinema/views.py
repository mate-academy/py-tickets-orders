from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from cinema import utils
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
    OrderSerializer, OrderListSerializer,
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

        queryset = queryset.prefetch_related("genres", "actors")

        filter_queryset = utils.extract_param_ids(
            self.request.query_params,
            "genres",
        )

        filter_queryset.update(utils.extract_param_ids(
            self.request.query_params,
            "actors",
        ))

        title = self.request.query_params.get("title", None)
        if title:
            filter_queryset.update({"title__icontains": title})

        return queryset.filter(**filter_queryset)

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

        if self.action == "list":
            queryset = queryset.select_related("movie", "cinema_hall")

            cinema_hall_capacity = (
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
            )
            queryset = queryset.annotate(
                tickets_available=cinema_hall_capacity - Count("tickets")
            )

        filter_queryset = {}

        date = self.request.query_params.get("date", None)
        if date:
            try:
                filter_date = datetime.strptime(date, "%Y-%m-%d").date()
                filter_queryset.update({"show_time__date": filter_date})
            except ValueError:
                raise ValidationError(
                    {"date": "Invalid date format. Use YYYY-MM-DD"}
                )

        filter_queryset.update(utils.extract_param_ids(
            self.request.query_params,
            "movie",
        ))

        return queryset.filter(**filter_queryset)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.select_related("user")
            queryset = queryset.prefetch_related(
                "tickets",
                "tickets__movie_session",
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "tickets",
            )

        return queryset

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer
