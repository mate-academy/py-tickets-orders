from datetime import datetime

from django.db.models import F, Count
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
    OrderSerializer
)


def parse_query_to_ints(param):
    return [int(item) for item in param.split(",")]


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
    queryset = Movie.objects.prefetch_related("genres", "actors").all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        elif self.action == "retrieve":
            return MovieDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = self.queryset

        genres_param = self.request.query_params.get("genres")
        actors_param = self.request.query_params.get("actors")
        title_param = self.request.query_params.get("title")

        if self.action == "list":
            if genres_param:
                genre_ids = parse_query_to_ints(genres_param)
                queryset = queryset.filter(genres__id__in=genre_ids)

            if actors_param:
                actor_ids = parse_query_to_ints(actors_param)
                queryset = queryset.filter(actors__id__in=actor_ids)

            if title_param:
                queryset = queryset.filter(title__icontains=title_param)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        MovieSession.objects.select_related
        ("movie", "cinema_hall").prefetch_related("tickets").all()
    )
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = self.queryset.annotate(
            available_tickets=F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row") - Count("tickets")
        )

        show_time_param = self.request.query_params.get("date")
        movie_param = self.request.query_params.get("movie")

        if self.action == "list":
            if show_time_param:
                date = datetime.strptime(show_time_param, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date)

            if movie_param:
                queryset = queryset.filter(movie__id=int(movie_param))

        return queryset.distinct()


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (
        Order.objects.prefetch_related
        ("tickets__movie_session__movie",
         "tickets__movie_session__cinema_hall"
         ).all()
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
