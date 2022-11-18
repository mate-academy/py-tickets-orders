from django.db.models import Q, Count, F
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
    OrderListSerializer,
    OrderCreateSerializer,
)


class StandardPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 1000


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
    queryset = Movie.objects.all().prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    @staticmethod
    def _search_convert(search_val):
        return [int(val) for val in search_val.split(",")]

    def get_queryset(self):
        actors = self.request.query_params.get("actors", 0)
        title = self.request.query_params.get("title", 0)
        genres = self.request.query_params.get("genres", 0)

        if title:
            self.queryset = self.queryset.filter(title__icontains=title)
        if genres:
            self.queryset = self.queryset.filter(
                genres__id__in=self._search_convert(genres)
            ).distinct()
        if actors:
            self.queryset = self.queryset.filter(
                actors__id__in=self._search_convert(actors)
            ).distinct()
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all().select_related(
        "movie", "cinema_hall"
    )
    serializer_class = MovieSessionSerializer

    @staticmethod
    def _search_convert(search_val):
        return [int(val) for val in search_val.split(",")]

    def get_queryset(self):
        movie = self.request.query_params.get("movie", 0)
        date = self.request.query_params.get("date", 0)

        if movie:
            self.queryset = self.queryset.filter(
                movie__id__in=self._search_convert(movie)
            ).distinct()
        if date:
            self.queryset = self.queryset.filter(
                show_time__date=date
            ).distinct()

        return self.queryset.annotate(
            tickets_available=F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row")
            - Count("tickets")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related(
        "tickets__movie_session__cinema_hall", "tickets__movie_session__movie"
    )
    serializer_class = OrderListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)

        return self.queryset.filter(id=-1)  # :P

    def get_serializer_class(self):
        if self.action == "create":
            self.serializer_class = OrderCreateSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
