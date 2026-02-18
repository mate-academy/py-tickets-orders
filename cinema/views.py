from django.db.models import Prefetch, F, Count
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if genres:
            genre_ids = convert_string_to_list(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)

        if actors:
            actor_ids = convert_string_to_list(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        queryset = queryset.distinct()
        return queryset.prefetch_related("genres", "actors")


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
        queryset = MovieSession.objects.all()

        queryset = queryset.annotate(
            tickets_available=(F("cinema_hall__seats_in_row")
                               * F("cinema_hall__rows")
                               - Count("tickets")
                               )
        )

        movie_id = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie_id:
            queryset = queryset.filter(movie=int(movie_id))
        queryset = queryset.distinct()

        return queryset.select_related("movie", "cinema_hall")


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        ticket_qs = Ticket.objects.select_related(
            "movie_session__movie",
            "movie_session__cinema_hall"
        )

        queryset = (
            Order.objects.filter(user=self.request.user).prefetch_related(
                Prefetch("tickets", queryset=ticket_qs)
            ))
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def convert_string_to_list(query: str) -> list:
    return [int(q.strip()) for q in query.split(",") if q.strip()]
