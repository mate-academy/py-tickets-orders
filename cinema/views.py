from rest_framework import viewsets
from django.db.models import Count, F
from django.utils.dateparse import parse_date
from rest_framework.pagination import PageNumberPagination
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderSerializer,
    OrderListSerializer
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
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)
        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = [int(x) for x in genres.split(",") if x.strip().isdigit()]
            queryset = queryset.filter(genres__id__in=genres_ids)
        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = [int(x) for x in actors.split(",") if x.strip().isdigit()]
            queryset = queryset.filter(actors__id__in=actors_ids)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionDetailSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset().select_related("cinema_hall")
        queryset = queryset.annotate(
            tickets_available=F("cinema_hall__seats_in_row") * F("cinema_hall__rows") - Count("tickets")
        ).order_by("id")
        date_str = self.request.query_params.get("date")
        if date_str:
            queryset = queryset.filter(show_time__date=parse_date(date_str))
        movie_id = self.request.query_params.get("movie")
        if movie_id and movie_id.isdigit():
            queryset = queryset.filter(movie_id=int(movie_id))
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

class OrderPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 20

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__movie_session__cinema_hall")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
