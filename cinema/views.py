from datetime import datetime

from django.db.models import Count, F
from django.template.context_processors import request
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
    MovieSessionRetrieveSerializer,
    MovieListSerializer,
    OrderListSerializer, OrderSerializer, TicketSerializer,
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
    def _params_to_ints_(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors", None)
        if actors:
            actors = self._params_to_ints_(actors)
            queryset = queryset.filter(actors__id__in=actors)

        genres = self.request.query_params.get("genres", None)
        if genres:
            genres = self._params_to_ints_(genres)
            queryset = queryset.filter(genres__id__in=genres)

        title = self.request.query_params.get("title", None)
        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")
        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    @staticmethod
    def _params_to_ints_(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionRetrieveSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        show_time = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if show_time and movie:
            show_time_date = datetime.strptime(show_time, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=show_time_date)
            movie = self._params_to_ints_(movie)
            queryset = queryset.filter(movie__id__in=movie)
        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .prefetch_related("tickets", "movie__genres", "movie__actors")
                .annotate(
                    tickets_available=F(
                        "cinema_hall__seats_in_row"
                    ) - Count("tickets")
                )).order_by("id")

        if self.action == "retrieve":
            queryset = queryset.select_related("cinema_hall", "movie")
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
