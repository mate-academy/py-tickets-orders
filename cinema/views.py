from datetime import timezone, datetime

from django.db.models import Count, F, ExpressionWrapper, IntegerField
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
    MovieSessionRetrieveSerializer,
    MovieListSerializer,
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        genres_filter = self.request.query_params.get("genres")

        if genres_filter:
            queryset = queryset.filter(
                genres__in=self._parse_genres_param(genres_filter)
            ).distinct()

        actors_filter = self.request.query_params.get("actors")
        if actors_filter:
            queryset = queryset.filter(
                actors__id__in=self._parse_genres_param(actors_filter)
            ).distinct()

        title_filter = self.request.query_params.get("title")
        if title_filter:
            queryset = queryset.filter(title__icontains=title_filter)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset

    @staticmethod
    def _parse_genres_param(param):
        return [int(genre.strip())
                for genre in param.split(",")
                if genre.strip().isdigit()]


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionRetrieveSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        if self.action == "list":
            qs = MovieSession.objects.all().select_related("cinema_hall")
            qs = qs.annotate(
                taken=Count("tickets"),
                capacity=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row"),
                    output_field=IntegerField()
                ),
                available=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets"),
                    output_field=IntegerField()
                )
            )

            movie_filter = self.request.query_params.get("movie")
            if movie_filter:
                qs = qs.filter(movie_id=movie_filter)

            date_filter = self.request.query_params.get("date")
            if date_filter:
                date_obj = parse_date(date_filter)
                if date_obj:
                    qs = qs.filter(show_time__date=date_obj)
            return qs

        elif self.action == "retrieve":
            return MovieSession.objects.all().select_related("cinema_hall")
        return MovieSession.objects.all()


class OrderPagination(PageNumberPagination):
    pass


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
