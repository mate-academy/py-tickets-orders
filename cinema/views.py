from typing import Type

from django.db.models import Count, F, QuerySet
from rest_framework import viewsets
from rest_framework.serializers import BaseSerializer

from cinema.models import Actor, CinemaHall, Genre, Movie, MovieSession, Order
from cinema.pagination import OrderViewSetPagination
from cinema.serializers import (ActorSerializer, CinemaHallSerializer,
                                GenreSerializer, MovieDetailSerializer,
                                MovieListSerializer, MovieSerializer,
                                MovieSessionDetailSerializer,
                                MovieSessionListSerializer,
                                MovieSessionSerializer, OrderListSerializer,
                                OrderSerializer)


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

    @staticmethod
    def _parse_ids(query_string: str) -> list[int]:
        return [int(id) for id in query_string.split(",")]

    def get_queryset(self) -> QuerySet[Movie]:
        queryset = super().get_queryset().prefetch_related("genres", "actors")

        if self.action == "list":
            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            title = self.request.query_params.get("title")

            if actors:
                actor_ids = self._parse_ids(actors)
                queryset = queryset.filter(actors__id__in=actor_ids)

            if genres:
                genre_ids = self._parse_ids(genres)
                queryset = queryset.filter(genres__id__in=genre_ids)

            if title:
                queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return MovieListSerializer
        elif self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()

    def get_queryset(self) -> QuerySet[MovieSession]:
        queryset = super().get_queryset().select_related()

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                ) - Count("tickets")
            )
            date = self.request.query_params.get("date")
            movie_id = self.request.query_params.get("movie")

            if date:
                queryset = queryset.filter(show_time__date=date)

            if movie_id:
                queryset = queryset.filter(movie__id=movie_id)

        return queryset.distinct()

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderViewSetPagination

    def get_queryset(self) -> QuerySet[Order]:
        queryset = super().get_queryset().filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        elif self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets__movie_session")

        return queryset

    def perform_create(self, serializer: OrderSerializer) -> None:
        serializer.save(user=self.request.user)

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
