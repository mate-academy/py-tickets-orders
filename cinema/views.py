from django.db import connection, reset_queries
from django.db.models import Q, Count, F, Prefetch
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import Actor, CinemaHall, Genre, Movie, MovieSession, Order, Ticket
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    MovieSessionSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        filters = Q()

        actors = self.request.query_params.getlist("actors")
        if actors:
            filters &= Q(actors__in=actors)

        genres = self.request.query_params.getlist("genres")
        if genres:
            genres = list(map(int, genres[0].split(",")))
            filters &= Q(genres__in=genres)

        title = self.request.query_params.get("title")
        if title:
            filters &= Q(title__icontains=title)

        return self.queryset.filter(filters) if filters else self.queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            self.queryset = (self.queryset.select_related()
                             .annotate(tickets_available=F("movie_session__cinema_hall__capacity") - Count("tickets")))
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        date_param = self.request.query_params.get("date")
        if date_param:
            queryset = queryset.filter(show_time__date=date_param)
        movie_param = self.request.query_params.get("movie")
        if movie_param:
            queryset = queryset.filter(movie=movie_param)
        return queryset


class OrderSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(user=user)
        if self.action == "list":
            tickets_qs = Ticket.objects.select_related("movie_session__cinema_hall", "movie_session__movie")
            queryset = queryset.prefetch_related(Prefetch("tickets", queryset=tickets_qs))
            # queryset = queryset.prefetch_related(
            #     "tickets__movie_session__cinema_hall",
            #     "tickets__movie_session__movie",
            # )
            return queryset
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "create":
            return OrderCreateSerializer
        elif self.action == "retrieve":
            return OrderDetailSerializer

        return OrderDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return serializer.save()
