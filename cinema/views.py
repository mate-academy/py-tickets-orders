from django.db.models import Count, F, ExpressionWrapper, IntegerField
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

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
    queryset = Movie.objects.all().prefetch_related("actors", "genres")
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all().select_related()
    serializer_class = MovieSessionSerializer

    def _params_to_ints(self, query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = (
                queryset.annotate(
                    capacity=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    ),
                    tickets_available=ExpressionWrapper(
                        F("capacity") - Count("tickets"),
                        output_field=IntegerField()
                    )
                )
            )
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            date = parse_date(date)
            if not date:
                raise ValidationError(
                    "Invalid date format. Expected format: YYYY-MM-DD."
                )
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=int(movie))
        return queryset.distinct().order_by("id")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 2


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("user")
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().select_related("movie_session", "order")
    serializer_class = TicketSerializer
