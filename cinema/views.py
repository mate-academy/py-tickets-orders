from django.db.models import (Count, F)
from rest_framework import viewsets

from cinema.models import (Genre,
                           Actor,
                           CinemaHall,
                           Movie,
                           MovieSession,
                           Ticket,
                           Order)

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
    TicketListSerializer,
    TicketCreateSerializer,
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
    queryset = Movie.objects.all().prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        genres = self.request.GET.get("genres")
        actors = self.request.GET.get("actors")
        title = self.request.GET.get("title")
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
    queryset = (MovieSession.objects.all()
                .select_related("movie", "cinema_hall"))
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        search_date = self.request.GET.get("date")
        movie_session_id = self.request.GET.get("movie")
        if self.action == "list":
            queryset = (queryset.annotate
                        (tickets_available=F("cinema_hall__rows") * F("cinema_hall__seats_in_row") - Count("tickets"))
                        .order_by("id"))
        if search_date:
            queryset = queryset.filter(show_time__date=search_date)
        if movie_session_id:
            movie_session_id = self._params_to_ints(movie_session_id)
            queryset = queryset.filter(movie__id__in=movie_session_id)
        return queryset.distinct()

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketListSerializer

    def get_queryset(self):
        queryset = self.queryset
        return queryset.select_related("movie_session",
                                       "movie_session__cinema_hall",
                                       "movie_session__movie")

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        return TicketCreateSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderCreateSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = (
                queryset
                .prefetch_related("tickets",
                                  "tickets__movie_session",
                                  "tickets__movie_session__cinema_hall",
                                  "tickets__movie_session__movie"))
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
