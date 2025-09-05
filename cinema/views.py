from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, F, Count

from cinema.filters import MovieSessionFilter, MovieFilter
from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order,
)
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
    TicketSerializer,
    TicketDetailSerializer,
    OrderSerializer,
    OrderDetailSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_class = MovieFilter
    pagination_class = None

    def get_queryset(self):
        return Movie.objects.prefetch_related(
            "genres", "actors"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend, )
    filterset_class = MovieSessionFilter
    pagination_class = None

    def get_queryset(self):
        queryset = MovieSession.objects.select_related(
            "movie", "cinema_hall"
        ).prefetch_related(
            "tickets"
        ).annotate(
            tickets_available=(
                F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    pagination_class = None

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Ticket.objects.filter(
                order__user=self.request.user
            ).select_related(
                "movie_session",
                "movie_session__movie",
                "movie_session__cinema_hall"
            )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return TicketDetailSerializer
        return TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(
                user=self.request.user
            ).prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "movie_session",
                        "movie_session__movie",
                        "movie_session__cinema_hall"
                    )
                )
            )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderDetailSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
