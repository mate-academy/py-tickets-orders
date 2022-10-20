from datetime import datetime

from django.db.models import Count, F
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


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def _params_to_ids(qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        query_set = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = self._params_to_ids(actors)
            query_set = query_set.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = self._params_to_ids(genres)
            query_set = query_set.filter(genres__id__in=genres_ids)

        if title:
            query_set = query_set.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            query_set = (query_set
                         .prefetch_related("genres")
                         .prefetch_related("actors"))

        return query_set.distinct()


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
        query_set = self.queryset

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
            query_set = query_set.filter(
                show_time__year=date.year,
                show_time__month=date.month,
                show_time__day=date.day
            )

        if movie:
            query_set = query_set.filter(movie_id=int(movie))

        if self.action in ("list", "retrieve"):
            query_set = (
                query_set
                .select_related("movie")
                .select_related("cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row") - Count("tickets")
                    )
                )
            )
        return query_set


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderSessionViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def get_queryset(self):
        query_set = self.queryset.filter(user=self.request.user)
        if self.action in ("list", "retrieve"):
            query_set = (
                query_set
                .select_related("user")
                .prefetch_related("tickets__movie_session")
                .prefetch_related("tickets__movie_session__cinema_hall")
            )
        return query_set

    def prefetch_related(self, serializer):
        serializer.save(user=self.request.user)
