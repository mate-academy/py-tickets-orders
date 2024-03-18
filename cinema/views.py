from datetime import datetime

from django.db.models import Count, F
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
    MovieListSerializer,
    OrderSerializer,
    OrderListSerializer,
)
from cinema.services import query_params_to_int_list


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
        queryset = Movie.objects.all()

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

        if genres := self.request.query_params.get("genres"):
            genres = query_params_to_int_list(genres)
            queryset = queryset.filter(genres__in=genres)

        if actors := self.request.query_params.get("actors"):
            actors = query_params_to_int_list(actors)
            queryset = queryset.filter(actors__in=actors)

        if title := self.request.query_params.get("title"):
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
        queryset = MovieSession.objects.all()

        if self.action in ("list", "retrieve"):
            queryset = (
                queryset.
                select_related("movie", "cinema_hall").
                prefetch_related("tickets")
            )

            if self.action == "list":
                queryset = (
                    queryset.
                    annotate(tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets"))
                    )
                ).order_by("id")

        if date := self.request.query_params.get("date"):
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if movie := self.request.query_params.get("movie"):
            queryset = queryset.filter(movie_id=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = (
            Order.objects.
            prefetch_related("tickets__movie_session").
            filter(user=self.request.user)
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
