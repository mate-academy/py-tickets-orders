from django.db.models import Count, F
from django.utils.dateparse import parse_date
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
    OrderSerializer,
    OrderListSerializer,
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

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

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
        queryset = self.queryset

        date = self.request.query_params.get("date")
        if date:
            date = parse_date(date)
            queryset = queryset.filter(show_time__date=date)

        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie_id=movie)

        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .annotate(
                    tickets_available=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("tickets__movie_session")
        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
