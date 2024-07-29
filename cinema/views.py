import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
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
)


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


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
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if self.action in ("list", "retrieve"):
            self.queryset.prefetch_related("actors", "genres")

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            self.queryset = self.queryset.filter(actors__in=actors_ids)

        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            self.queryset = self.queryset.filter(genres__in=genres_ids)

        if title:
            self.queryset = self.queryset.filter(title__icontains=title)

        return self.queryset.distinct()


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
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if self.action in ("list", "retrieve"):
            self.queryset = self.queryset.select_related("movie",
                                                         "cinema_hall")

        if movie:
            self.queryset = self.queryset.filter(movie__id=movie)

        if date:
            self.queryset = self.queryset.filter(
                show_time__date=datetime.datetime
                .strptime(date, "%Y-%m-%d").date()
            )

        if self.action == "list":
            self.queryset = self.queryset.annotate(
                tickets_available=(F("cinema_hall__rows")
                                   * F("cinema_hall__seats_in_row")
                                   - Count("tickets"))
            )

        return self.queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return (Order.objects.filter(user=self.request.user)
                .prefetch_related("tickets"))
