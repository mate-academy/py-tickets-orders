from django.db.models import Count, F
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, TicketSerializer,
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
    def _params_to_ints(query_string):
        try:
            return[int(str_id) for str_id in query_string.split(",")]
        except ValueError:
            return []

    def get_queryset(self):
        queryset=self.queryset

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            genres = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres)

        if actors:
            actors = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors)

        if title:
            queryset = queryset.filter(title__icontains=title)
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
    def _params_to_ints(query_string):
        try:
            return[int(str_id) for str_id in query_string.split(",")]
        except ValueError:
            return []

    def get_queryset(self):
        queryset = self.queryset

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if movie:
            movie = self._params_to_ints(movie)
            queryset = queryset.filter(movie__id__in=movie)

        if date:
            try:
                date_obj = parse_date(date)
                if date_obj is None:
                    raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD"})
                queryset = queryset.filter(show_time__date=date_obj)
            except ValueError:
                raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD"})

        if self.action == "list":
            queryset = (
                queryset
                .prefetch_related("movie")
                .annotate(tickets_available=F("cinema_hall__rows")*F("cinema_hall__seats_in_row")-Count("tickets"))
            )
        return queryset.distinct()



    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
