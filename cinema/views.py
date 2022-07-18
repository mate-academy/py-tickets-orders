from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession, Order
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
    MovieListSerializer, OrderSerializer, OrderCreateSerializer
)


class OrderPagination(PageNumberPagination):
    page_size = 3
    page_query_param = "page_size"
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

    @staticmethod
    def _get_list_of_id(params):
        return [str(str_id) for str_id in params.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()
        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = self._get_list_of_id(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)
        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = self._get_list_of_id(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)
        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset.select_related("cinema_hall", "movie")
        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie_id=int(movie))

        date = self.request.query_params.get("date")
        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(show_time=date)
        queryset = queryset.annotate(
            tickets_available=(
                F("cinema_hall__seats_in_row")
                * F("cinema_hall__rows")
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
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.all()
        # queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__movie_session")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return self.serializer_class
