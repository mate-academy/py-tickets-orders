from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket,
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
    OrderListSerializer,
    TicketSerializer,
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
    serializer_class = MovieSerializer

    @staticmethod
    def str_to_list(genres: str) -> list:
        return [int(char) for char in genres.split(",")]

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("actors", "genres")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")
        if genres:
            queryset = queryset.filter(genres__id__in=self.str_to_list(genres))
        if actors:
            queryset = queryset.filter(actors__id=actors)
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
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.select_related("movie", "cinema_hall")
        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
            movie = self.request.query_params.get("movie")
            date = self.request.query_params.get("date")
            if movie:
                queryset = queryset.filter(movie_id=movie)
            if date:
                date = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date)
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related(
        "movie_session", "movie_session__movie", "movie_session__cinema_hall"
    )
    serializer_class = TicketSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination

    def get_queryset(self):
        if self.action == "list":
            return (
                Order.objects.select_related("user")
                .prefetch_related(
                    "tickets",
                    "tickets__movie_session__movie",
                    "tickets__movie_session__cinema_hall",
                )
                .filter(user=self.request.user)
            )
        return Order.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
