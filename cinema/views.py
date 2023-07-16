from django.db.models import F, Count
from django.utils.datetime_safe import datetime
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


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


def filter_by_ids(queryset, field_name, ids):
    if ids:
        ids = [int(item) for item in ids.split(",")]
        queryset = queryset.filter(**{f"{field_name}__in": ids})
    return queryset


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            queryset = filter_by_ids(queryset, "genres", genres)

        if actors:
            queryset = filter_by_ids(queryset, "actors", actors)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action == ("list", "retrieve"):
            queryset = Movie.objects.prefetch_related("genres", "actors")

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

    def get_queryset(self):
        queryset = self.queryset

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            format_string = "%Y-%m-%d"
            date = datetime.strptime(date, format_string)
            queryset = queryset.filter(show_time__date=date.date())

        if movie:
            queryset = queryset.filter(movie=movie)

        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .prefetch_related("tickets")
                .annotate(
                    tickets_available=F(
                        "cinema_hall__seats_in_row"
                    ) * F("cinema_hall__rows") - Count("tickets")
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets__movie_session")
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.filter(user=self.request.user)
            return queryset

    def get_serializer_class(self):
        if self.action == "post":
            return OrderSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
