from django.db.models import Count, F, QuerySet
from rest_framework import viewsets
from rest_framework.serializers import ModelSerializer

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import OrderSetPagination
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
    OrderRetrieveSerializer,
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
    def _params_to_ints(query_string: str) -> queryset:
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            titles = self.request.query_params.get("title")

            if actors:
                actors = self._params_to_ints(actors)
                queryset = queryset.filter(actors__id__in=actors)
            elif genres:
                genres = self._params_to_ints(genres)
                queryset = queryset.filter(genres__id__in=genres)
            elif titles:
                queryset = queryset.filter(title__icontains=titles)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "genres",
                "actors"
            )
        return queryset.distinct()

    def get_serializer_class(self) -> ModelSerializer:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> queryset:
        queryset = super().get_queryset()
        if self.action == "list":
            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")

            if date:
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.filter(movie_id=movie)

        if self.action in "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .prefetch_related("tickets")
                .annotate(
                    capacity=(F("cinema_hall__rows")
                              * F("cinema_hall__seats_in_row")),
                    tickets_available=F("capacity") - Count("tickets"))
            )
        elif self.action == "retrieve":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .prefetch_related("tickets")
            )

        return queryset

    def get_serializer_class(self) -> ModelSerializer:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderSetPagination

    def get_queryset(self) -> QuerySet:
        queryset = Order.objects.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        return queryset

    def get_serializer_class(self) -> ModelSerializer:
        if self.action in ("list", "retrieve"):
            return OrderRetrieveSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
