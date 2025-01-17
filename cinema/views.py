from django.db.models import QuerySet, Count, F
from rest_framework import viewsets
from django.utils.dateparse import parse_date
from django.db.models.functions import Cast
from django.db.models import DateField
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

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = [
                int(actor) for actor in actors.split(",")
                if actor.isdigit()
            ]
            queryset = queryset.filter(actors__id__in=actors_ids)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = [
                int(genre) for genre in genres.split(",")
                if genre.isdigit()
            ]
            queryset = queryset.filter(genres__id__in=genres_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if self.action == "list":

            queryset = (
                queryset
                .annotate(available_places=F(
                    "cinema_hall__rows"
                ) * F("cinema_hall__seats_in_row") - Count("tickets"))
            )

            date_str = self.request.query_params.get("date")
            if date_str:
                date = parse_date(date_str)
                queryset = queryset.annotate(
                    show_date=Cast("show_time", DateField())
                ).filter(show_date=date)

            movie = self.request.query_params.get("movie")
            if movie:
                queryset = queryset.filter(movie__id=movie)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
        return queryset

    def get_serializer_class(self) -> object:
        serializer = OrderSerializer
        if self.action == "list":
            serializer = OrderListSerializer
        return serializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
