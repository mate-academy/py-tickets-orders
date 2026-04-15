from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import OrderListPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer,
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
        qs = super().get_queryset()
        if self.action == "list":
            capacity = (F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row"))

            qs = qs.annotate(
                tickets_available=capacity - Count("tickets", distinct=True)
            )

        movie = self.request.query_params.get("movie")
        if movie:
            qs = qs.filter(movie__id__in=self._parse_ids(movie))

        date = self.request.query_params.get("date")
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
                qs = qs.filter(show_time__date=date)
            except Exception:
                raise ValidationError({
                    "date": "Invalid date format. Use YYYY-MM-DD"})

        return qs.distinct()

    @staticmethod
    def _parse_ids(param):
        return [int(x.strip()) for x in param.split(",")
                if x.strip().isdigit()]


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    pagination_class = OrderListPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        actors = self.request.query_params.get("actors")
        if actors:
            qs = qs.filter(actors__id__in=self._parse_ids(actors))

        genres = self.request.query_params.get("genres")
        if genres:
            qs = qs.filter(genres__id__in=self._parse_ids(genres))

        title = self.request.query_params.get("title")
        if title:
            qs = qs.filter(title__icontains=title)

        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def _parse_ids(param):
        return [int(x.strip()) for x in param.split(",")
                if x.strip().isdigit()]
