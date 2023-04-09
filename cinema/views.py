from typing import Type

from django.db.models import QuerySet, F, Count
from django.utils.datetime_safe import datetime
from rest_framework import viewsets
from rest_framework.serializers import Serializer

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order
)
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
    TicketSerializer,
    OrderListSerializer,
    TicketListSerializer,
    OrderCreateSerializer
)


def query_params_str_to_int(queryset):
    return [int(id_) for id_ in queryset.split(",")]


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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    #
    def get_queryset(self) -> QuerySet:
        title = self.request.query_params.get("title")
        if title:
            queryset = Movie.objects.filter(title__contains=title)
            return queryset

        actors = self.request.query_params.get("actors")
        if actors:
            list_id = query_params_str_to_int(actors)
            queryset = Movie.objects.filter(actors__id__in=list_id)
            return queryset

        genres = self.request.query_params.get("genres")
        if genres:
            list_id = query_params_str_to_int(genres)
            queryset = Movie.objects.filter(genres__id__in=list_id)
            return queryset

        return self.queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.select_related("cinema_hall")
        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )

            movies = self.request.query_params.get("movie")
            date = self.request.query_params.get("date")
            if movies:
                movies_id = query_params_str_to_int(movies)
                queryset = queryset.filter(movie_id__in=movies_id)
            if date:
                date_to_filter = datetime.strptime(date, "%Y-%m-%d")
                queryset = queryset.filter(
                    show_time__date=date_to_filter
                )
        return queryset


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return TicketListSerializer
        return TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
