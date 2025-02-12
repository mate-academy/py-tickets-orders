from django.db.models import F, Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.filters import BaseFilterBackend
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


class MovieFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        title_param = request.query_params.get('title')
        actors_param = request.query_params.get('actors')
        genres_param = request.query_params.get('genres')

        if title_param:
            queryset = queryset.filter(title__icontains=title_param)

        if actors_param:
            queryset = queryset.filter(actors__id=actors_param)

        if genres_param:
            genres_ids = [int(str_id) for str_id in genres_param.split(',')]
            queryset = queryset.filter(genres__id__in=genres_ids)

        return queryset


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filter_backends = [MovieFilterBackend]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class DateAndMovieFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        date_param = request.query_params.get('date')
        movie_param = request.query_params.get('movie')

        if date_param:
            try:
                date = timezone.datetime.strptime(date_param, '%Y-%m-%d').date()
                queryset = queryset.filter(show_time__date=date)
            except ValueError:
                pass

        if movie_param:
            queryset = queryset.filter(movie__id=movie_param)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    filter_backends = [DateAndMovieFilterBackend]

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall")
                .annotate(tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                ) - Count("tickets"))
            ).order_by("id")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class MessagesPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "per_page"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = MessagesPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
