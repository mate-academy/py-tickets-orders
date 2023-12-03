from datetime import datetime

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone

from cinema.models import (Genre, Actor, CinemaHall,
                           Movie, MovieSession, Order, Ticket)

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
    OrderListSerializer
)


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


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

    def get_queryset(self):
        queryset = self.queryset

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title", "")

        if genres:
            queryset = queryset.filter(
                genres__id__in=[int(s) for s in genres.split(",")]
            )

        if actors:
            queryset = queryset.filter(
                actors__id__in=[int(s) for s in actors.split(",")]
            )

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            queryset = (
                queryset
                .prefetch_related("genres")
                .prefetch_related("actors")
            )

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

    def get_queryset(self):
        queryset = self.queryset

        movie = self.request.query_params.get("movie")
        date_param = self.request.query_params.get("date", None)

        if movie:
            queryset = queryset.filter(
                movie__id__in=[int(s) for s in movie.split(",")]
            )

        if date_param:
            date = datetime.strptime(date_param, "%Y-%m-%d")
            date = timezone.make_aware(
                timezone.datetime(date.year, date.month, date.day)
            )
            queryset = queryset.filter(show_time__date=date)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer
