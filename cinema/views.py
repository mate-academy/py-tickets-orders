from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
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
    OrderSerializer,
    TicketSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderPagination,
)


class GenreViewSet(viewsets.ModelViewSet):
    serializer_class = GenreSerializer
    queryset = Genre.objects.all()

    def get_queryset(self):
        name = self.request.query_params.get("name")
        if name:
            self.queryset = self.queryset.filter(name__icontains=name)
        return self.queryset


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer

    def get_queryset(self):
        queryset = Actor.objects.all()
        first_name = self.request.query_params.get("first_name")
        if first_name:
            queryset = Actor.objects.filter(first_name__icontains=first_name)
        return queryset


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        queryset = super().get_queryset()
        if title:
            queryset = Movie.objects.filter(title__icontains=title)
        if genres:
            genres_id = [int(genre) for genre in genres.split(",")]
            queryset = Movie.objects.filter(genres__in=genres_id)
        if actors:
            queryset = Movie.objects.filter(actors=actors)
        return queryset


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
        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.select_related(
                "cinema_hall", "movie"
            ).annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )
        if date:
            date_object = datetime.strptime(date, "%Y-%m-%d")
            queryset = MovieSession.objects.filter(
                show_time__date=date_object.date()
            )
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)
        return queryset


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        if self.action == "list":
            self.queryset = self.queryset.filter(user=self.request.user)
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderSerializer
        return OrderDetailSerializer
