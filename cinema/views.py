from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from rest_framework.pagination import PageNumberPagination

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
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        title = self.request.query_params.get("title", None)
        if title:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres", None)
        if genres:
            genres = genres.split(",")
            queryset = queryset.filter(genres__id__in=genres)

        actors = self.request.query_params.get("actors", None)
        if actors:
            actors = actors.split(",")
            queryset = queryset.filter(actors__id__in=actors)

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

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        date = self.request.query_params.get("date", None)
        if date:
            queryset = queryset.filter(show_time__date=date)

        movie = self.request.query_params.get("movie", None)
        if movie:
            queryset = queryset.filter(movie__id=movie)
        return queryset.distinct()


class OrderPagination(PageNumberPagination):
    page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = Order.objects.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer: OrderSerializer) -> None:
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> type[Serializer]:
        if self.action == "list":
            return OrderListSerializer

        return super().get_serializer_class()
