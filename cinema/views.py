from rest_framework import viewsets
from cinema.pagination import OrderPagination
from datetime import datetime

from django.db.models import Count, F

from cinema.models import (
    Genre, Actor,
    CinemaHall, Movie,
    MovieSession, Order,
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
    TicketSerializer,
    OrdersSerializer,
    OrderListSerializer,
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

    @staticmethod
    def _params_to_ints(str_ids: str) -> list[int]:
        return [int(str_id) for str_id in str_ids.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if self.action in ("list", "retrieve"):
            queryset = (
                Movie
                .objects
                .prefetch_related("actors")
                .prefetch_related("genres")
            )

        if actors:
            actors_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

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

        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if self.action == "list":
            queryset = (
                MovieSession
                .objects
                .select_related("movie")
                .annotate(tickets_available=F(
                    "cinema_hall__rows")
                    * F("cinema_hall__seats_in_row") - Count("tickets"))
            ).order_by("id")

        if date:
            queryset = (
                queryset
                .filter(
                    show_time__contains=datetime
                    .strptime(
                        date,
                        "%Y-%m-%d"
                    )
                    .strftime("%Y-%m-%d")
                )
            )

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrdersSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.request == "list":
            return OrderListSerializer
        return OrdersSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = (
                queryset
                .prefetch_related("tickets__movie_session__cinema_hall")
                .prefetch_related("tickets__movie_session__movie")
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
