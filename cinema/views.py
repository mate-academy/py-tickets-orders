from datetime import datetime
from typing import Type

from django.db.models import (
    F,
    Count,
    QuerySet
)
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import Serializer

from cinema.models import (
    Actor,
    Genre,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
)

from cinema.serializers import (
    ActorSerializer,
    GenreSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    OrderListSerializer,
    TicketSerializer,
    TicketListSerializer,
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    @staticmethod
    def _param_to_ints(qs) -> list:
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres is not None:
            genres_ids = self._param_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if actors is not None:
            actors_ids = self._param_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if title is not None:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer

    @staticmethod
    def _params_to_int(qs) -> list:
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if date is not None:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(
                show_time__date=date
            )

        if movie is not None:
            movie_ids = self._params_to_int(movie)
            queryset = queryset.filter(movie__id__in=movie_ids)

        if self.action in ("list", "retrieve"):
            queryset = queryset.annotate(
                tickets_available=F(
                    "cinema_hall__rows") * F(
                    "cinema_hall__seats_in_row") - Count("tickets")
            )

        return queryset.distinct()

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return TicketListSerializer
        return TicketSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        if self.action == "list":
            user = self.request.user
            if user.is_authenticated:
                queryset = queryset.filter(user__exact=user)
        return queryset

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
