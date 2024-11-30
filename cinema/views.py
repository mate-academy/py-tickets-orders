from django.db.models import F, Count, QuerySet
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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


def _params_to_ints(qs):
    return [int(str_id) for str_id in qs.split(",")]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all().prefetch_related("actors", "genres")
    serializer_class = MovieSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors:
            actors_id = _params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_id)

        if genres:
            genres_id = _params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_id)

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
    queryset = MovieSession.objects.all().select_related("movie",
                                                         "cinema_hall")
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie:
            movie_ids = _params_to_ints(movie)
            queryset = queryset.filter(movie__id__in=movie_ids)

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets"))

        return queryset.distinct()


class OrderPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page-size"
    max_page_size = 1000


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer
