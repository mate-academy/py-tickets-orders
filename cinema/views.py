from __future__ import annotations

from typing import Type

from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    QuerySet,
)
from django.utils.dateparse import parse_date
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    MovieSessionWriteSerializer,
    MovieWriteSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
)


def _parse_int_list(value: str) -> list[int]:
    result = []
    for part in value.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


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

    def get_queryset(self) -> QuerySet[Movie]:
        qs = super().get_queryset()

        title = self.request.query_params.get("title")
        if title:
            qs = qs.filter(title__icontains=title)

        genres = self.request.query_params.get("genres")
        if genres:
            genre_ids = _parse_int_list(genres)
            if genre_ids:
                qs = qs.filter(genres__id__in=genre_ids)

        actors = self.request.query_params.get("actors")
        if actors:
            actor_ids = _parse_int_list(actors)
            if actor_ids:
                qs = qs.filter(actors__id__in=actor_ids)

        return qs.distinct()

    def get_serializer_class(self) -> Type[serializers.Serializer]:
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieWriteSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        MovieSession.objects.select_related(
            "movie",
            "cinema_hall",
        )
        .prefetch_related(
            "movie__genres",
            "movie__actors",
        )
        .annotate(
            tickets_sold=Count("tickets", distinct=True),
            hall_capacity=ExpressionWrapper(
                F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row"),
                output_field=IntegerField(),
            ),
        )
        .annotate(
            tickets_available=ExpressionWrapper(
                F("hall_capacity") - F("tickets_sold"),
                output_field=IntegerField(),
            )
        )
    )

    def get_queryset(self) -> QuerySet[MovieSession]:
        qs = super().get_queryset()

        date_str = self.request.query_params.get("date")
        if date_str:
            date_value = parse_date(date_str)
            if date_value:
                qs = qs.filter(show_time__date=date_value)

        movie = self.request.query_params.get("movie")
        if movie and movie.isdigit():
            qs = qs.filter(movie_id=int(movie))

        return qs

    def get_serializer_class(self) -> Type[serializers.Serializer]:
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionWriteSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet[Order]:
        return (
            super()
            .get_queryset()
            .filter(user=self.request.user)
            .prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self) -> Type[serializers.Serializer]:
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
