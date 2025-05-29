import datetime

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
    MovieListSerializer, OrderTicketRetrieveSerializer, OrderTicketSerializer,
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
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()
        actors = self.request.GET.get("actors")
        genres = self.request.GET.get("genres")
        title = self.request.GET.get("title")

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.all()
        date = self.request.GET.get("date")
        movie = self.request.GET.get("movie")

        if date:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=movie)
        return queryset


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderTicketRetrieveSerializer
        return OrderTicketSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related("tickets")
        return queryset
