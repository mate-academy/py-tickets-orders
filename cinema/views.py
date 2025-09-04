from django.db.models import F
from django.db.models.aggregates import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

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
    OrderListSerializer, OrderCreateSerializer, MovieSessionFilter,
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
        qs = Movie.objects.all()
        title_param = self.request.query_params.get("title")
        genres_param = self.request.query_params.get("genres")
        actors_param = self.request.query_params.get("actors")

        if title_param:
            qs = qs.filter(title__icontains=title_param)

        if genres_param:
            try:
                genres = [int(g) for g in genres_param.split(",")]
                qs = qs.filter(genres__id__in=genres).distinct()
            except ValueError:
                qs = qs.none()

        if actors_param:
            try:
                actors = [int(a) for a in actors_param.split(",")]
                qs = qs.filter(actors__id__in=actors).distinct()
            except ValueError:
                qs = qs.none()

        return qs.prefetch_related("genres", "actors").distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = MovieSessionFilter
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset.select_related("movie", "cinema_hall")
        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=F(
                    "cinema_hall__rows") * F(
                    "cinema_hall__seats_in_row") - Count("tickets")
            )
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderCreateSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
