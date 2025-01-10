from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets
from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    Order,
    Ticket,
    MovieSession,
)
from cinema.pagination import OrdersPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    TicketSerializer,
    OrderDetailSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    MovieSessionSerializer,
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
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        queryset = Movie.objects.all()

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = Movie.objects.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = Movie.objects.filter(genres__id__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ["retrieve", "list"]:
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionListSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        elif self.action == "create":
            return MovieSessionSerializer
        return MovieSessionListSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        queryset = MovieSession.objects.all()
        if movie:
            try:
                movie_ids = [int(str_id) for str_id in movie.split(",")]
                queryset = queryset.filter(movie_id__in=movie_ids)
            except ValueError:
                raise ValidationError(
                    {"movie": "Invalid movie ID. Must be an integer."}
                )

        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=parsed_date)
            except ValueError:
                raise ValidationError(
                    {"date": "Invalid date format. Use YYYY-MM-DD."}
                )

        if self.action in ["retrieve", "list"]:
            queryset = queryset.prefetch_related("movie")

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrdersPagination

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return OrderSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
