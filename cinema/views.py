from django.db.models import F, Count
from django.template.context_processors import request
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
    OrderSerializer,
    OrderPagination,
    OrderCreateSerializer,
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
    pagination_class = None

    def get_queryset(self):
        qs = self.queryset

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            qs = qs.filter(genres__id__in=genres_ids)

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            qs = qs.filter(actors__id__in=actors_ids)

        title = self.request.query_params.get("title")
        if title:
            qs = qs.filter(title__icontains=title)

        if self.action == "list":
            qs = qs.prefetch_related("genres", "actors")

        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self):
        qs = self.queryset

        if movies := self.request.query_params.get("movie"):
            movies_ids = [int(str_id) for str_id in movies.split(",")]
            qs = qs.filter(movie__id__in=movies_ids)

        if date := self.request.query_params.get("date"):
            qs = qs.filter(show_time__date=date)

        if self.action == "list":
            qs = qs.annotate(
                tickets_available=F(
                    "cinema_hall__rows"
                ) * F(
                    "cinema_hall__seats_in_row"
                ) - Count(
                    "tickets"
                )
            )

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer
