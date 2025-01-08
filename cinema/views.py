from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
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
    OrderSerializer,
)
from cinema.filters import MovieFilter, MovieSessionFilter
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from rest_framework.viewsets import ModelViewSet


class OrderPagination(PageNumberPagination):
    page_size = 10


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets").all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = MovieFilter
    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


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
