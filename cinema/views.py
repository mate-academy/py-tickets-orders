from datetime import datetime
from typing import Type
from django.db.models import QuerySet, Count, F
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response
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
    OrderListSerializer
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

    @staticmethod
    def _filter_by_params(
        query_string: str,
        param_name: str,
        queryset: QuerySet = None
    ) -> QuerySet:
        try:
            id_list = [int(str_id) for str_id in query_string.split(",")]
            return queryset.filter(**{f"{param_name}__id__in": id_list})
        except ValueError:
            raise serializers.ValidationError(
                f"Invalid query string: {query_string}. IDs must be integers."
            )

    def get_queryset(self) -> QuerySet:
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        try:
            if genres:
                self.queryset = self._filter_by_params(
                    genres,
                    "genres",
                    self.queryset
                )

            if actors:
                self.queryset = self._filter_by_params(
                    actors,
                    "actors",
                    self.queryset
                )

            if title:
                self.queryset = self.queryset.filter(title__icontains=title)

            return self.queryset
        except Exception as e:
            raise serializers.ValidationError(
                f"Failed to filter queryset: {str(e)}"
            )

    def get_serializer_class(self) -> Type[serializers.BaseSerializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()

    def get_queryset(self) -> QuerySet:
        self.queryset = self.queryset.select_related(
            "movie",
            "cinema_hall"
        ).annotate(
            tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
            ) - Count("tickets")
        )

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Please use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            self.queryset = self.queryset.filter(show_time__date=date)

        if movie:
            try:
                movie = int(movie)
            except ValueError:
                return Response(
                    {"error": "Invalid movie ID. Please provide an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            self.queryset = self.queryset.filter(movie__id=movie)

        return self.queryset

    def get_serializer_class(self) -> Type[serializers.BaseSerializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderViewSetPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )
        return queryset

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """ Associate the newly created order with the authenticated user. """
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> Type[serializers.BaseSerializer]:
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer
