from django.db.models import QuerySet
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

    @staticmethod
    def _turn_params_to_int(params: str) -> list[int]:
        return [int(param) for param in params.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("actors", "genres")
        actor_ids = self.request.query_params.get("actors")
        genre_ids = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actor_ids:
            queryset = queryset.filter(actors__in=self._turn_params_to_int(actor_ids))

        if genre_ids:
            queryset = queryset.filter(genres__in=self._turn_params_to_int(genre_ids))

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.prefetch_related(
            "cinema_hall", "movie"
        )

        if self.action == "list":
            session_date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            if session_date:
                queryset = queryset.filter(show_time__date=session_date)
            if movie:
                queryset = queryset.filter(movie=movie)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = Order.objects.prefetch_related(
            "tickets__movie_session",
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie",
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
