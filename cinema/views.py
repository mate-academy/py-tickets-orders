from django.db.models import Count, F
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
    MovieListSerializer, OrderSerializer, OrderListSerializer,
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
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    def get_queryset(self):
        qs = self.queryset
        actors = self.request.query_params.get("actors")
        if actors:
            actors_id = [
                int(actor_id) for actor_id in actors.split(",")
                if actor_id.isdigit()
            ]
            qs = qs.filter(actors__id__in=actors_id)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_id = [
                int(genre_id) for genre_id in genres.split(",")
                if genre_id.isdigit()
            ]
            qs = qs.filter(genres__id__in=genres_id)

        title = self.request.query_params.get("title")
        if title:
            qs = qs.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            qs = qs.prefetch_related("genres", "actors")

        return qs.distinct()


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
        qs = self.queryset
        movie = self.request.query_params.get("movie")
        if movie:
            qs = qs.filter(movie_id__in=[int(movie)])

        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(show_time__date=date)

        if self.action == "list":
            qs = qs.select_related("movie", "cinema_hall").annotate(
                tickets_available=F(
                    "cinema_hall__rows"
                ) * F(
                    "cinema_hall__seats_in_row"
                ) - Count("tickets")
            )
            return qs

        if self.action == "retrieve":
            return qs.select_related("movie", "cinema_hall")
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user)
        if self.action in ("list", "retrieve"):
            return qs.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve") :
            return OrderListSerializer
        return self.serializer_class
