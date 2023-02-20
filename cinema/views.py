from django.db.models import F, Count, QuerySet
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from rest_framework import serializers
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
    OrderPagination,
    TicketSerializer,
    TicketListSerializer,
    OrderCreateSerializer,
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    @staticmethod
    def get_id_from_str(string_queryset: str) -> list[int]:
        return [int(string) for string in string_queryset.split(",")]

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            queryset = queryset.filter(
                actors__id__in=self.get_id_from_str(actors)
            )
        if genres:
            queryset = queryset.filter(
                genres__id__in=self.get_id_from_str(genres)
            )
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self) -> type[serializers.Serializer]:
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
            queryset = queryset.filter(movie_id=int(movie))
        if self.action == "list":
            queryset = (
                queryset.select_related("cinema_hall", "movie").annotate(
                    tickets_available=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            ).order_by("id")
            return queryset

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination
    queryset = Order.objects.select_related("user")
    serializer_class = OrderListSerializer

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer: serializer_class) -> None:
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "list":
            return OrderListSerializer
