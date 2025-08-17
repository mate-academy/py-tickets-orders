from django.db import transaction
from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

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
    OrderListSerializer,
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

    def _params_to_ints(self, qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = Movie.objects.all()
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
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()

    def _params_to_ints(self, qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = MovieSession.objects.all()
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            movie = self._params_to_ints(movie)
            queryset = queryset.filter(movie__id__in=movie)

        if self.action == "list":
            total_place = (F("cinema_hall__rows")
                           * F("cinema_hall__seats_in_row"))
            queryset = queryset.annotate(
                tickets_available=total_place - Count("tickets")
            ).order_by("id")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class SetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    pagination_class = SetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(user=self.request.user)
            tickets_data = self.request.data.get("tickets")
            for ticket_data in tickets_data:
                Ticket.objects.create(
                    order=order,
                    row=ticket_data["row"],
                    seat=ticket_data["seat"],
                    movie_session_id=ticket_data["movie_session"],
                )
