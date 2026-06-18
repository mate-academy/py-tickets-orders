from django.db.models import Prefetch, F, Count
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order
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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

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
        if actors:
            actors = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors)
        if genres:
            genres = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if movie:
            queryset = queryset.filter(movie_id=movie)
        if date:
            queryset = queryset.filter(show_time__date=date)
        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = OrderListSerializer
        return serializer
