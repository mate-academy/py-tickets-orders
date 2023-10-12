from datetime import datetime
import re

from django.db.models import F, Count, QuerySet
from django.utils.timezone import make_aware
from rest_framework import viewsets
from rest_framework.serializers import BaseSerializer

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

    def get_queryset(self) -> QuerySet[Movie]:
        queryset = self.queryset

        if title := self.request.query_params.get("title"):
            queryset = queryset.filter(title__icontains=title)

        if actors := self.request.query_params.get("actors"):
            actor_ids = [
                int(actor_id)
                for actor_id in actors.split(",")
                if actor_id.isnumeric()
            ]
            if actor_ids:
                queryset = queryset.filter(actors__id__in=actor_ids)

        if genres := self.request.query_params.get("genres"):
            genre_ids = [
                int(genre_id)
                for genre_id in genres.split(",")
                if genre_id.isnumeric()
            ]
            if genre_ids:
                queryset = queryset.filter(genres__id__in=genre_ids)

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

    def get_queryset(self) -> QuerySet[MovieSession]:
        queryset = self.queryset.annotate(
            tickets_available=F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row")
            - Count("tickets")
        )

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("movie", "cinema_hall")

        if (
            date_param := self.request.query_params.get("date")
        ) and re.fullmatch(
            r"^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$", date_param
        ):
            date_obj = make_aware(datetime.strptime(date_param, "%Y-%m-%d"))
            queryset = queryset.filter(show_time__date=date_obj.date())

        if movie_param := self.request.query_params.get("movie"):
            queryset = queryset.filter(movie_id=movie_param)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet[Order]:
        queryset = self.queryset.filter(user=self.request.user)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )

        return queryset

    def get_serializer_class(self) -> type[BaseSerializer[Order]]:
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer: BaseSerializer[Order]) -> None:
        serializer.save(user=self.request.user)
