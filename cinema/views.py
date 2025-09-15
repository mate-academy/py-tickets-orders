from django.db.models import Q
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, \
    Ticket, Order
from cinema.pagination import OrderPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, TicketSerializer, OrderSerializer,
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

    def list_ids(self, param):
        return [int(pk) for pk in param.split(",") if
                pk.strip().isdigit()]

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related(
            "actors", "genres"
        )
        actors_params = self.request.query_params.get("actors")
        genres_params = self.request.query_params.get("genres")
        title_params = self.request.query_params.get("title")

        if actors_params:
            actors_ids = self.list_ids(actors_params)
            queryset = queryset.filter(
                Q(actors__id__in=actors_ids)
            )
        if genres_params:
            genre_ids = self.list_ids(genres_params)
            queryset = queryset.filter(
                Q(genres__id__in=genre_ids)
            )
        if title_params:
            queryset = queryset.filter(
                Q(title__icontains=title_params)
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.prefetch_related("tickets")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.all()
        movie_params = self.request.query_params.get("movie")
        date_params = self.request.query_params.get("date")
        if movie_params:
            movie_id = [int(pk) for pk in movie_params.split(",") if
                        pk.strip().isdigit()]
            queryset = queryset.filter(
                Q(movie__id__in=movie_id)
            )

        if date_params:
            queryset = queryset.filter(
                Q(show_time__date=date_params)
            )
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
