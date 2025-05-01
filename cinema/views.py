from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import datetime
from rest_framework.response import Response

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
    MovieListSerializer,
    MovieDetailSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
)


class PaginatedViewSet(viewsets.ModelViewSet):
    def get_paginated_response(self, data):
        if self.paginator and self.request.query_params.get("page", None):
            return self.paginator.get_paginated_response(data)
        return Response(data)


class GenreViewSet(PaginatedViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(PaginatedViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(PaginatedViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(PaginatedViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        queryset = Movie.objects.all()
        title = self.request.query_params.get("title", None)
        genres = self.request.query_params.get("genres", "").split(",")
        actors = self.request.query_params.get("actors", "").split(",")

        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres and genres[0]:
            try:
                genre_ids = [int(g) for g in genres]
                queryset = queryset.filter(genres__id__in=genre_ids).distinct()
            except (ValueError, TypeError):
                return Movie.objects.none()
        if actors and actors[0]:
            try:
                actor_ids = [int(a) for a in actors]
                queryset = queryset.filter(actors__id__in=actor_ids).distinct()
            except (ValueError, TypeError):
                return Movie.objects.none()

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(PaginatedViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = MovieSession.objects.all()
        date = self.request.query_params.get("date", None)
        movie = self.request.query_params.get("movie", None)

        if date is not None:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date_obj)
            except ValueError:
                return MovieSession.objects.none()
        if movie is not None:
            try:
                movie_id = int(movie)
                queryset = queryset.filter(movie_id=movie_id)
            except ValueError:
                return MovieSession.objects.none()

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(PaginatedViewSet):
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderCreateSerializer
