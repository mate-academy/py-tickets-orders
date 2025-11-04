import datetime

from django.db.models import Q
from rest_framework import viewsets, permissions
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
    OrderSerializer,
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
    queryset = CinemaHall.objects.all().order_by("id")
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres")
        if genres:
            try:
                if "," in genres:
                    genre_ids = [int(g.strip()) for g in genres.split(",")]
                    queryset = queryset.filter(genres__id__in=genre_ids)
                else:
                    genre_id = int(genres)
                    queryset = queryset.filter(genres__id=genre_id)
            except ValueError:
                queryset = queryset.filter(genres__name__icontains=genres)

        actors = self.request.query_params.get("actors")
        if actors:
            try:
                if "," in actors:
                    actor_ids = [int(a.strip()) for a in actors.split(",")]
                    queryset = queryset.filter(actors__id__in=actor_ids)
                else:
                    actor_id = int(actors)
                    queryset = queryset.filter(actors__id=actor_id)
            except ValueError:
                queryset = queryset.filter(
                    Q(actors__first_name__icontains=actors)
                    | Q(actors__last_name__icontains=actors)
                )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        movie_id = self.request.query_params.get("movie")
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
