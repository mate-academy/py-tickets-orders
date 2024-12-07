import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import LargeResultsSetPagination
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


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieFilter(django_filters.FilterSet):
    genres = django_filters.NumberFilter(field_name="genres__id")
    actors = django_filters.NumberFilter(field_name="actors__id")
    title = django_filters.CharFilter(
        field_name="title", lookup_expr="icontains"
    )

    class Meta:
        model = Movie
        fields = ["genres", "actors", "title"]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MovieFilter

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(
        field_name="show_time", lookup_expr="date"
    )
    movie = django_filters.NumberFilter(field_name="movie_id")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MovieSessionFilter

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
