from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre, Actor, CinemaHall, Movie,
    MovieSession, Order, Ticket,
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

        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset

        if actors := self.request.query_params.get("actors"):
            actors_id = actors.split(",")
            queryset = queryset.filter(actors__id__in=actors_id)

        if genres := self.request.query_params.get("genres"):
            genres_id = genres.split(",")
            queryset = queryset.filter(genres__id__in=genres_id)

        if self.request.query_params.get("title"):
            queryset = queryset.filter(
                title__icontains=self.request.query_params.get("title")
            )

        if self.action == "list":
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset.distinct()


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
        queryset = self.queryset

        if movie_id := self.request.query_params.get("movie"):
            queryset = queryset.filter(movie_id=movie_id)

        if date := self.request.query_params.get("date"):
            date = date.rstrip("/")
            queryset = queryset.filter(
                show_time__date=datetime.strptime(date, "%Y-%m-%d").date()
            )

        if self.action == "list":
            queryset = (
                (
                    queryset.select_related("movie", "cinema_hall")
                    .prefetch_related("tickets")
                    .annotate(
                        tickets_available=(
                            F("cinema_hall__rows")
                            * F("cinema_hall__seats_in_row")
                            - Count("tickets")
                        )
                    )
                )
                .order_by("id")
                .distinct()
            )

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user.pk)

        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer

        return self.serializer_class


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("movie_session")
    serializer_class = TicketSerializer
