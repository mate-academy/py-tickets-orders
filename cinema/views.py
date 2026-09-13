from datetime import datetime

from django.db.models import Count, F
from django.utils.dateparse import parse_date
from rest_framework import viewsets
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
    OrderListSerializer,
    OrderSerializer,
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
        actors = self.request.query_params.get("actors", None)
        genres = self.request.query_params.get("genres", None)
        title = self.request.query_params.get("title", None)

        queryset = self.queryset.prefetch_related("genres", "actors")
        if actors:
            queryset = queryset.filter(actors__in=actors.split(","))

        if genres:
            queryset = queryset.filter(genres__in=genres.split(","))

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            movie_id = self.request.query_params.get("movie", None)
            show_time_date = self.request.query_params.get("date", None)

            if movie_id:
                queryset = queryset.filter(movie_id=int(movie_id))

            if show_time_date:
                parsed_date = parse_date(show_time_date)
                if parsed_date:
                    start_of_day = datetime.combine(
                        parsed_date,
                        datetime.min.time()
                    )
                    end_of_day = datetime.combine(
                        parsed_date,
                        datetime.max.time()
                    )
                    queryset = queryset.filter(
                        show_time__range=(start_of_day, end_of_day)
                    )

            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")))
            )
        return queryset


class OrderListPagination(PageNumberPagination):
    page_size = 1


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets__movie_session")
    serializer_class = OrderListSerializer
    pagination_class = OrderListPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer) -> None:
        return serializer.save(user=self.request.user)
