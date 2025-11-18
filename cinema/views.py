from datetime import datetime

from django.db.models import F, Count, ExpressionWrapper, IntegerField
from django.utils.dateparse import parse_date
from rest_framework import viewsets

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
    OrderSerializer, OrderListSerializer,
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
        queryset = super().get_queryset()
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        string = self.request.query_params.get("string")
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(
                actors__id__in=actors_ids
            )
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(
                genres__id__in=genres_ids
            )
        if title:
            queryset = queryset.filter(
                title=title
            )
        if string:
            queryset = queryset.filter(
                title__icontains=string
            )

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
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            date_obj = datetime.fromisoformat(date).date()
            queryset = queryset.filter(show_time__date=date_obj)
        if movie:
            queryset = queryset.filter(movie=movie)

        if self.action == "list":
            queryset = (queryset
                        .select_related("cinema_hall")
                        .prefetch_related("tickets")
                        .annotate(
                            tickets_available=ExpressionWrapper(
                                F("cinema_hall__rows")
                                * F("cinema_hall__seats_in_row")
                                - Count("tickets"),
                                output_field=IntegerField(),
                            )
                        )
                        )
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = (Order.objects
                    .filter(user=self.request.user)
                    .prefetch_related(
                        "tickets",
                        "tickets__movie_session__movie",
                        "tickets__movie_session__cinema_hall",
                    )
                    )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
