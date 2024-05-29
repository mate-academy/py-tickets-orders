from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
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
    queryset = Movie.objects.prefetch_related("actors", "genres")
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            queryset = queryset.filter(actors__id=actors)
        if genres:
            genres = [int(genre) for genre in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.prefetch_related("cinema_hall", "movie")
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if movie:
            queryset = queryset.filter(movie_id=movie)
        if date:
            queryset = queryset.filter(show_time__date=date)

        if self.action in "list":
            queryset = queryset.select_related().annotate(
                tickets_available=F("cinema_hall__seats_in_row") * F("cinema_hall__rows") - Count("tickets")
            )
        elif self.action in "retrieve":
            queryset = queryset.select_related().annotate(
                taken_places=Count("tickets")
            )

        return queryset


class SmallSetPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page_size"
    max_page_size = 50


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets")
    serializer_class = OrderSerializer
    pagination_class = SmallSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
