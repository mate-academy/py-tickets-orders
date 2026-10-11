from datetime import datetime

from django.db.models import Prefetch, F, Count
from rest_framework import viewsets, permissions
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

        return MovieSerializer

    @staticmethod
    def _params_to_ints(qs):
        """'1,2,3' -> [1, 2, 3]"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            title = self.request.query_params.get("title")
            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")

            if title:
                queryset = queryset.filter(title__contains=title)
            if actors:
                queryset = queryset.filter(
                    actors__id__in=self._params_to_ints(actors)
                )
            if genres:
                queryset = queryset.filter(
                    genres__id__in=self._params_to_ints(genres)
                )
        return queryset.distinct().order_by("id")


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

        if self.action == "retrieve":
            queryset = queryset.select_related(
                "cinema_hall", "movie"
            ).prefetch_related("tickets")

        if self.action == "list":
            queryset = queryset.select_related("movie", "cinema_hall")
            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")

            if date:
                date = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.filter(movie_id=movie)

            queryset = queryset.annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )

        return queryset


class OrderPagination(PageNumberPagination):
    max_page_size = 100
    page_size = 3


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "movie_session__movie", "movie_session__cinema_hall"
                    ),
                )
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        match self.action:
            case "list":
                return OrderListSerializer
            case "create":
                return OrderCreateSerializer
            case _:
                return OrderCreateSerializer
