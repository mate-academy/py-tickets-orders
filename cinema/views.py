from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets, pagination

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
    OrderListSerializer,
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


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors is not None:
            actors_ids = [
                int(str_id) for str_id in actors.split(",")
            ]
            queryset = queryset.filter(
                actors__id__in=actors_ids
            )

        if genres is not None:
            genres_ids = [
                int(str_id) for str_id in genres.split(",")
            ]
            queryset = queryset.filter(
                genres__id__in=genres_ids
            )

        if title is not None:
            queryset = queryset.filter(
                title__icontains=title
            )

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "actors", "genres"
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects

        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie is not None:
            queryset = queryset.filter(movie=movie)

        if date is not None:
            date_ = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(
                show_time__date=date_
            )

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "movie", "cinema_hall", "tickets"
            ).annotate(tickets_available=F("cinema_hall__rows")
                       * F("cinema_hall__seats_in_row")
                       - Count("tickets"))

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects
    serializer_class = OrderListSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
