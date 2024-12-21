import re
from rest_framework.response import Response

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from datetime import datetime
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
    TicketSerializer
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer

    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        title = self.request.query_params.get("title", None)
        actors = self.request.query_params.get("actors", None)
        genres = self.request.query_params.get("genres", None)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__in=genres_ids)

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__in=actors_ids)

        return queryset.distinct()

    def paginate_queryset(self, queryset):
        return None


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer

    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie__id=movie)

        date = self.request.query_params.get("date")
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date_obj)
            except ValueError:
                return queryset.none()

        queryset = queryset.annotate(
            tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        ).order_by("id")

        return queryset.distinct()


class OrderPagination(PageNumberPagination):
    page_size = 5


class OrderListCreateView(viewsets.ModelViewSet):
    pagination_class = OrderPagination


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
