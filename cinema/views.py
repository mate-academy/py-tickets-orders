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
)


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


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

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        queryset = Movie.objects.all()

        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            queryset = queryset.filter(actors__id=actors)
        if genres:
            genre_ids = genres.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids).distinct()
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        queryset = MovieSession.objects.prefetch_related("tickets")

        if movie:
            queryset = queryset.filter(movie_id=int(movie))
        if date:
            queryset = queryset.filter(show_time__date=date)
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    pagination_class = Pagination

    def get_queryset(self):
        return Order.objects.all().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
