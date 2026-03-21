from django.db.models import Count, F
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
    TicketSerializer,
    OrderSerializer,
    OrderCreateSerializer,
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


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors").all()
    serializer_class = MovieSerializer
    pagination_class = None

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
            queryset = queryset.filter(actors__in=self._parse_parm(actors))

        if genres:
            queryset = queryset.filter(genres__in=self._parse_parm(genres))

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    @staticmethod
    def _parse_parm(parms):
        if parms:
            return [parm for parm in parms.split(",")]


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

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie:
            queryset = queryset.filter(movie_id=movie)

        return queryset.annotate(
            Count("tickets"),
            tickets_available=F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row")
            - Count("tickets")
        )


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            ))

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
