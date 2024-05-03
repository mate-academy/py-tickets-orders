from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

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
    OrderSerializer,
    TicketDetailSerializer,
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
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actor_ids = [int(actor_id) for actor_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actor_ids)

        if genres:
            genre_ids = [int(genre_id) for genre_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genre_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        queryset = queryset.prefetch_related("actors", "genres")

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
            queryset = queryset.select_related().annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )

        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date:
            data_obj = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(show_time__date=data_obj)

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset.order_by("id")


class OrderSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 1


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderSerializer

        elif self.action == "retrieve":
            return TicketDetailSerializer

        return OrderSerializer
