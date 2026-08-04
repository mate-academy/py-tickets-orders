from datetime import datetime

from django.db.models import F, Count
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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    @staticmethod
    def params_to_inst(qs: str) -> list[int]:
        return [int(str_id)
                for str_id in qs.split(",")
                if str_id.isdigit()
                ]

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("genres", "actors")

        title = self.request.query_params.get("title")
        genre = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genre:
            genre_ids = self.params_to_inst(genre)
            queryset = queryset.filter(genres__id__in=genre_ids)

        if actors:
            actor_ids = self.params_to_inst(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    @staticmethod
    def params_to_ints(qs: str) -> list[int]:
        return [
            int(str_id)
            for str_id in qs.split(",")
            if str_id.isdigit()
        ]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            total_seats = (
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
            )
            queryset = (
                queryset.annotate(
                    tickets_available=total_seats - Count("tickets")
                )
                .select_related("movie", "cinema_hall")
            )

        if self.action == "retrieve":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .prefetch_related("tickets")
            )

        date_str = self.request.query_params.get("date")
        movie_ids_str = self.request.query_params.get("movie")

        if date_str:
            queryset = queryset.filter(show_time__date=date_str)

        if movie_ids_str:
            movie_ids = self.params_to_ints(movie_ids_str)
            queryset = queryset.filter(movie_id__in=movie_ids)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
