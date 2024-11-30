from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
)

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


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title", None)
        genres = self.request.query_params.get("genres", None)
        actors = self.request.query_params.get("actors", None)

        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres:
            genre_ids = genres.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids)
        if actors:
            queryset = queryset.filter(actors__id=actors)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        MovieSession.objects.all()
        .select_related("movie")
        .prefetch_related("tickets")
    )
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_query = self.request.query_params.get("date", None)
        movie = self.request.query_params.get("movie", None)

        if date_query:
            date = parse_date(date_query)
            if date:
                queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie__id=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related("tickets")
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
