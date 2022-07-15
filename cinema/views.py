from datetime import datetime

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
    OrderSerializer, OrderCreateSerializer
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


class ParamsToIntsMixin:
    @staticmethod
    def _params_to_ints(qs):
        return [int(str_id) for str_id in qs.split(",")]


class MovieViewSet(viewsets.ModelViewSet, ParamsToIntsMixin):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = self._params_to_ints(actors)
            queryset = self.queryset.filter(actors__id__in=actors_ids)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = self._params_to_ints(genres)
            queryset = self.queryset.filter(genres__id__in=genres_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = self.queryset.filter(
                actors__movie__title__icontains=title
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet, ParamsToIntsMixin):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset.select_related("movie", "cinema_hall")
        movies = self.request.query_params.get("movie")
        if movies:
            movies_ids = self._params_to_ints(movies)
            queryset = self.queryset.filter(movie__id__in=movies_ids)

        filter_date = self.request.query_params.get("date")
        if filter_date:
            queryset = queryset.filter(
                show_time=datetime.strptime(filter_date, "%Y-%m-%d")
            )

        queryset = (
            queryset.annotate(
                tickets_available=(
                    F("cinema_hall__seats_in_row")
                    * F("cinema_hall__rows")
                    - Count("tickets")
                )
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
    page_size = 1
    page_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__movie_session")

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

