from rest_framework import viewsets
from rest_framework import serializers

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Ticket, Order
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
    TicketWriteSerializer,
    OrderSerializer,
    OrderCreateSerializer,
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TicketWriteSerializer
        return TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action in ["create"]:
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
