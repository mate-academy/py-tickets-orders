from django.db.models import F
from django.db.models.aggregates import Count
from django.db.models.functions import Greatest, Coalesce
from rest_framework import viewsets, permissions
from rest_framework.pagination import LimitOffsetPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
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
)


class OrderPagination(LimitOffsetPagination):
    default_limit = 10


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
        queryset = self.queryset
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")
        if genres:
            ids = [int(x) for x in genres.split(",") if x.strip().isdigit()]
            if ids:
                queryset = queryset.filter(genres__id__in=ids)
        if actors:
            ids = [int(x) for x in actors.split(",") if x.strip().isdigit()]
            if ids:
                queryset = queryset.filter(actors__id__in=ids)
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

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
            queryset = queryset.filter(movie__id=movie)
        if self.action == "list":
            queryset = (
                queryset.select_related("cinema_hall")
                .annotate(
                    taken=Coalesce(Count("tickets"), 0),
                    cinema_hall_capacity=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row"),
                )
                .annotate(
                    tickets_available=Greatest(
                        F("cinema_hall_capacity") - F("taken"), 0
                    )
                )
                .order_by("id")
            )
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination
    queryset = Order.objects
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (self.queryset.filter(
                user=self.request.user)
                .order_by("-created_at"))
