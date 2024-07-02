from django.db.models import Q, Count, F
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
    OrderListSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 10


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
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        title = self.request.query_params.get("title", None)
        genres = self.request.query_params.get("genres", None)
        actors = self.request.query_params.get("actors", None)

        if genres:
            genres_ids = [int(genre_id) for genre_id in genres.split(",")]
            self.queryset = self.queryset.filter(genres__id__in=genres_ids)
        if title:
            self.queryset = self.queryset.filter(title__icontains=title)
        if actors:
            actors_ids = [int(actors_id) for actors_id in actors.split(",")]
            self.queryset = self.queryset.filter(actors__id__in=actors_ids)
        return self.queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date", None)
        movie_id = self.request.query_params.get("movie", None)
        if self.action == "list":
            self.queryset = self.queryset.prefetch_related(
                "cinema_hall", "movie", "tickets"
            ).annotate(
                tickets_available=F(
                    "cinema_hall__rows"
                ) * F(
                    "cinema_hall__seats_in_row"
                ) - Count("tickets")
            )
        if date:
            self.queryset = self.queryset.filter(show_time__date=date)
        if movie_id:
            self.queryset = self.queryset.filter(movie_id=movie_id)
        return self.queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__movie"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
