from typing import Type

from django.db.models import QuerySet, Q
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def _search_by_params(
            self,
            title: str,
            actors: str,
            genres: str
    ) -> QuerySet:
        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

        if actors:
            queryset = queryset.filter(
                Q(actors__first_name__icontains=actors)
                | Q(actors__last_name__icontains=actors)
            )

        if genres:
            queryset = queryset.filter(genres__name__icontains=genres)

        return queryset.distinct()

    def get_queryset(self):
        queryset = self.queryset

        all_params = {
            "title": self.request.query_params.get("title"),
            "actors": self.request.query_params.get("actors"),
            "genres": self.request.query_params.get("genres")
        }

        if all_params:
            return self._search_by_params(**all_params)

        return queryset

    def get_serializer_class(self) -> Type[
        MovieListSerializer
        | MovieDetailSerializer
        | MovieSerializer
    ]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self) -> Type[
        MovieSessionListSerializer
        | MovieSessionDetailSerializer
        | MovieSessionSerializer
    ]:
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
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")

        return queryset

    def get_serializer_class(self) -> Type[
        OrderListSerializer
        | OrderSerializer
    ]:
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
