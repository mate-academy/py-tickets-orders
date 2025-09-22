from datetime import datetime
from typing import List

from django.db.models import Count, F
from rest_framework import viewsets, pagination

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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):

        def get_ids(param_str: str) -> List[int]:
            return [int(id) for id in param_str.split(",") if id.isdigit()]

        queryset = Movie.objects.all()
        if self.action == "list":
            queryset = queryset.prefetch_related("genres", "actors")

        params = self.request.query_params

        actors = params.get("actors")
        if actors is not None:
            actor_ids = get_ids(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)

        genres = params.get("genres")
        if genres is not None:
            genre_ids = get_ids(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)

        title = params.get("title")
        if title is not None:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        elif self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie",
                                "cinema_hall")
                .prefetch_related("tickets")
                .annotate(
                    available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        if self.action == "retrieve":
            queryset = self.queryset.prefetch_related("tickets")

        params = self.request.query_params

        movie = params.get("movie")
        if movie is not None:
            queryset = (
                queryset
                .filter(movie__id=int(movie))
            )

        session_date = params.get("date")
        if session_date is not None:
            date_obj = datetime.strptime(session_date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date_obj)

        return queryset


class OrderPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        if self.action == "list":
            queryset = self.queryset.prefetch_related("tickets")
        queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
