
from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket

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
    OrderSerializer, OrderListSerializer,
    # TicketSerializer,
    # OrderListSerializer,
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
        if self.action == "retrieve":
            return MovieDetailSerializer

        if self.action == "list":
            return MovieListSerializer
        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()

        # Filter by genres
        genres = self.request.query_params.getlist('genres', [])
        if genres:
            queryset = queryset.filter(genres__name__in=genres)

        # Filter by actors (first_name and last_name)
        actors = self.request.query_params.getlist('actors', [])
        if actors:
            actor_filters = Q()
            for actor_name in actors:
                actor_name_parts = actor_name.split()
                if len(actor_name_parts) == 2:
                    first_name, last_name = actor_name_parts
                    actor_filters |= Q(actors__first_name__icontains=first_name) & Q(actors__last_name__icontains=last_name)
            queryset = queryset.filter(actor_filters)

        # Filter by title (contains)
        title = self.request.query_params.get('title', None)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionListSerializer
    filter_backends = [filters.OrderingFilter]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_param = self.request.query_params.get("date")
        print("date_param:", date_param)  # Додайте цей рядок
        movie_id_param = self.request.query_params.get("movie")

        if date_param:
            try:
                date_param = datetime.strptime(date_param, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date_param)
            except ValueError:
                queryset = queryset.none()

        if movie_id_param:
            queryset = queryset.filter(movie_id=movie_id_param)

        return queryset



class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer
