from django.db.models import Prefetch, F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order, Ticket,
)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderSerializer,
    OrderListSerializer, TicketSerializer, TicketListSerializer,
)


class ParseParamsMixin:
    @staticmethod
    def _parse_params(query_string) -> list[int]:
        return [int(str_id) for str_id in query_string.split(",")]


class GenreViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(ParseParamsMixin, viewsets.ModelViewSet):
    pagination_class = None

    def get_queryset(self):
        queryset = Movie.objects.all()

        if actors := self.request.query_params.get("actors"):
            actors_ids = self._parse_params(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres := self.request.query_params.get("genres"):
            genres_ids = self._parse_params(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if title := self.request.query_params.get("title"):
            queryset = queryset.filter(title__icontains=title)

        if self.action == "list":
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(ParseParamsMixin, viewsets.ModelViewSet):
    pagination_class = None

    def get_queryset(self):
        queryset = MovieSession.objects.all()

        if movies := self.request.query_params.get("movie"):
            movies_ids = self._parse_params(movies)
            queryset = queryset.filter(movie__id__in=movies_ids)

        if date := self.request.query_params.get("date"):
            queryset = queryset.filter(show_time__date=date)

        return queryset.select_related(
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Ticket.objects.filter(
            order__user=self.request.user
        ).select_related(
            "movie_session__movie",
            "movie_session__cinema_hall"
        )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return TicketListSerializer
        return TicketSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 50


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "movie_session__movie",
                        "movie_session__cinema_hall"
                    )
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
