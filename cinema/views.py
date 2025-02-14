from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.response import Response

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
    OrderCreateSerializer
)
from cinema.pagination import CustomPagination
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all().order_by("id")
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all().order_by("id")
    serializer_class = MovieSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response(response.data["results"])
        return response

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("genres", "actors")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_list = list(map(int, actors.split(",")))
            queryset = queryset.filter(actors__id__in=actors_list)
        if genres:
            genres_list = list(map(int, genres.split(",")))
            queryset = queryset.filter(genres__id__in=genres_list)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all().order_by("id")
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = (self.queryset.prefetch_related("movie", "cinema_hall")
                    .annotate(
            capacity=F("cinema_hall__rows"
                       ) * F("cinema_hall__seats_in_row"),
            tickets_available=F("capacity") - Count("tickets")
        ).order_by("id"))

        date_str = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date_obj)
            except ValueError:
                pass
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = CustomPagination

    def get_queryset(self):
        return self.queryset.prefetch_related(
            "tickets__movie_session",
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        ).filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer
