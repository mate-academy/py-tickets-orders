from datetime import datetime

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
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
    OrderSerializer,
    AnonymousUserOrderSerializer,
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

    def get_queryset(self):
        queryset = Movie.objects.all()
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            actors_filters = Q(actors__id__in=actors_ids)
            queryset = queryset.filter(actors_filters)

        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            genre_filters = Q(genres__id__in=genres_ids)
            queryset = queryset.filter(genre_filters)

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

    def get_queryset(self):
        queryset = MovieSession.objects.all()
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if date:
            date_object = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(show_time__date=date_object)

        if movie:
            queryset = queryset.filter(movie_id=movie)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if isinstance(self.request.user, AnonymousUser):
            return AnonymousUserOrderSerializer
        return OrderSerializer
