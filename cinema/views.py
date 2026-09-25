from __future__ import annotations

from datetime import datetime

from django.db.models import Count, F, Prefetch, QuerySet
from rest_framework import mixins, serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession
from cinema.models import Order, Ticket

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


def parse_ids(value: str, parameter: str) -> list[int]:
    """Parse comma-separated positive IDs or return a client error."""
    try:
        identifiers = [int(item) for item in value.split(",")]
        if any(identifier < 1 for identifier in identifiers):
            raise ValueError
    except ValueError as error:
        raise ValidationError(
            {parameter: "Provide comma-separated positive integer IDs."}
        ) from error
    return identifiers


class GenreViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self) -> QuerySet[Movie]:
        queryset = super().get_queryset().prefetch_related("genres", "actors")
        for parameter in ("genres", "actors"):
            value = self.request.query_params.get(parameter)
            if value is not None:
                queryset = queryset.filter(
                    **{f"{parameter}__id__in": parse_ids(value, parameter)}
                )
        title = self.request.query_params.get("title")
        if title is not None:
            queryset = queryset.filter(title__icontains=title)
        return queryset.distinct()

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> QuerySet[MovieSession]:
        queryset = super().get_queryset().select_related(
            "movie", "cinema_hall"
        ).annotate(
            tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        ).order_by("-show_time", "-pk")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "movie__genres", "movie__actors", "tickets"
            )
        date = self.request.query_params.get("date")
        if date is not None:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError as error:
                raise ValidationError(
                    {"date": "Provide a valid date in YYYY-MM-DD format."}
                ) from error
            queryset = queryset.filter(show_time__date=parsed_date)
        movie = self.request.query_params.get("movie")
        if movie is not None:
            identifiers = parse_ids(movie, "movie")
            if len(identifiers) != 1:
                raise ValidationError({"movie": "Provide one movie ID."})
            queryset = queryset.filter(movie_id=identifiers[0])
        return queryset

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Only authenticated users can list and create their own orders."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get_queryset(self) -> QuerySet[Order]:
        sessions = MovieSession.objects.select_related(
            "movie", "cinema_hall"
        ).annotate(
            tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        )
        tickets = Ticket.objects.prefetch_related(
            Prefetch("movie_session", queryset=sessions)
        )
        return Order.objects.filter(user=self.request.user).prefetch_related(
            Prefetch("tickets", queryset=tickets)
        ).order_by("-created_at", "-pk")

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer: OrderSerializer) -> None:
        serializer.save(user=self.request.user)
