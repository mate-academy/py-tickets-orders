from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    MovieSessionFullListSerializer,
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
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        queryset = self.queryset.all()

        if title:
            queryset = queryset.filter(
                title__icontains=title
            ).distinct()
        if actors:
            actors_ids = [int(id_str) for id_str in actors.split(",")]
            queryset = queryset.filter(
                actors__id__in=actors_ids
            ).distinct()
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(
                genres__id__in=genres_ids
            ).distinct()

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionFullListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
                .order_by("id")
            )

            date = self.request.query_params.get("date")
            movie_id = self.request.query_params.get("movie")

            if date:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                queryset = queryset.filter(show_time__date=date_obj)
            if movie_id:
                queryset = queryset.filter(
                    movie__id=movie_id
                )
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderSerializer
        return OrderCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
