from django.db.models import Q, Count, F
from rest_framework import viewsets
from datetime import datetime

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import OrderPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, OrderListSerializer,
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

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = [int(actor) for actor in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)

        elif genres:
            genres_ids = [int(genre) for genre in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)

        elif title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

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

        movie_id = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        filters = Q()
        if date:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            filters &= Q(show_time__date=date_obj)
        if movie_id:
            filters &= Q(movie_id=movie_id)

        if filters:
            queryset = queryset.filter(filters)

        if self.action == "retrieve":
            queryset = queryset.select_related("movie", "cinema_hall")

        elif self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    ) - Count("tickets")
                )
                .order_by("id")
            )

        return queryset


class OrderSessionViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action in ("list", "retrieve"):
            queryset = (
                queryset
                .select_related("user")
                .prefetch_related("tickets__movie_session")
            )

        order_id = self.request.query_params.get("order")
        if order_id:
            queryset = queryset.filter(id=order_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
