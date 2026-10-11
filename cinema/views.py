from django.db.models import Count, F
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    OrderListSerializer,
    MovieSessionFullSerializer,
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        queryset = self.queryset
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = (queryset
                        .filter(actors__id__in=actors_ids)
                        .prefetch_related("actors"))
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = (queryset
                        .filter(genres__id__in=genres_ids)
                        .prefetch_related("genres"))
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionFullSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset
                .select_related()
                .annotate(
                    tickets_available=F(
                        "cinema_hall__rows") * F(
                        "cinema_hall__seats_in_row") - Count(
                        "tickets", distinct=True))
            )

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            movie_ids = [int(str_id) for str_id in movie.split(",")]
            queryset = (queryset
                        .filter(movie__id__in=movie_ids)
                        .select_related("movie")
                        .select_related("cinema_hall"))
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return self.serializer_class
        return OrderListSerializer

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.filter(
                user=self.request.user
            ).prefetch_related("tickets__movie_session")
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
