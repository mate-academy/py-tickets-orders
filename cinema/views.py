from datetime import datetime
from rest_framework import viewsets, filters
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
        # Фільтрування за акторами (по імені та прізвищу)
        actors = self.request.query_params.getlist("actors", [])
        if actors:
            queryset = queryset.filter(actors__in=actors)

        # Фільтрування за жанрами
        genre_ids = self.request.query_params.get("genres", None)
        if genre_ids:
            genre_ids = genre_ids.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids)

        # Фільтрування за назвою (містить рядок)
        title_contains = self.request.query_params.get("title", None)
        if title_contains:
            queryset = queryset.filter(title__icontains=title_contains)

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
