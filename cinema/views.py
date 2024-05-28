from typing import Type, List

from django.db.models import (
    Q,
    Count,
    F,
    ExpressionWrapper,
    IntegerField,
    QuerySet
)
from django.utils.dateparse import parse_date
from rest_framework import viewsets, serializers

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import OrderSetPagination
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionGeneralSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    OrderCreateSerializer,
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
    def params_to_int(query_string: str) -> List[int]:
        return [int(param) for param in query_string.split(",")]

    def get_queryset(self) -> QuerySet[Movie]:
        queryset = self.queryset

        actors = self.request.query_params.get("actors", None)
        genres = self.request.query_params.get("genres", None)
        title = self.request.query_params.get("title", None)

        if actors:
            actors = self.params_to_int(actors)
            queryset = queryset.filter(actors__in=actors)
        if genres:
            genres = self.params_to_int(genres)
            queryset = queryset.filter(genres__in=genres)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionGeneralSerializer

    def get_queryset(self) -> QuerySet[MovieSession]:
        queryset = self.queryset

        movie = self.request.query_params.get("movie", None)
        date = self.request.query_params.get("date", None)

        if movie:
            queryset = queryset.filter(movie__id=movie)
        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                queryset = queryset.filter(show_time__date=parsed_date)

        if self.action == "list":
            queryset = queryset.select_related(
                "movie", "cinema_hall"
            ).prefetch_related(
                "tickets"
            )

            queryset = queryset.annotate(
                cinema_hall_capacity=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row"),
                    output_field=IntegerField(),
                ),
                tickets_count=Count("tickets"),
            ).annotate(
                tickets_available=F(
                    "cinema_hall_capacity"
                ) - F("tickets_count")
            )

        return queryset.distinct()

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionGeneralSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self) -> QuerySet[Order]:
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer: serializers.ModelSerializer) -> None:
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.action == "list":
            return self.serializer_class
        return OrderCreateSerializer
