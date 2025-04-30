from django.db.models import Count, F
from rest_framework import viewsets

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order, Ticket,
)
from cinema.pagination import StandardResultsSetPagination

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
    OrderListSerializer, TicketSerializer, TicketListSerializer,
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

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title", None)
        if title:
            return queryset.filter(title__icontains=title)

        actors = self.request.query_params.get("actors", None)
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = (queryset.filter(actors__id__in=actors_ids))

        genres = self.request.query_params.get("genres", None)
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = (queryset.filter(genres__id__in=genres_ids))

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")
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

        date = self.request.query_params.get("date", None)
        if date:
            queryset = queryset.filter(show_time__date=date)

        movie = self.request.query_params.get("movie", None)
        if movie:
            queryset = queryset.filter(movie_id=int(movie))

        if self.action == "list":
            queryset = queryset.select_related("movie", "cinema_hall")
            queryset = (queryset.annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets"))
            )

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            return (
                self.queryset.filter(user=self.request.user).prefetch_related(
                    "tickets__movie_session",
                    "tickets__movie_session__cinema_hall",
                    "tickets__movie_session__movie")
            )
        elif self.action == "retrieve":
            return (self.queryset.filter(user=self.request.user).
                    prefetch_related("tickets__movie_session"))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
