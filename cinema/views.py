from django.db.models import F
from django.db.models.aggregates import Count
from rest_framework import viewsets

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
    OrderCreateSerializer,
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
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        qs = self.queryset

        if self.action == "list":
            actors_params, genres_params, title_search = (
                self.request.query_params.get("actors"),
                self.request.query_params.get("genres"),
                self.request.query_params.get("title"),
            )
            if actors_params:
                actors_params = [
                    int(actor_id)
                    for actor_id in actors_params.split(",")
                    if actor_id.isdigit()
                ]
                qs = qs.filter(actors__id__in=actors_params)
            if genres_params:
                genres_params = [
                    int(genre_id)
                    for genre_id in genres_params.split(",")
                    if genre_id.isdigit()
                ]
                qs = qs.filter(genres__id__in=genres_params)
            if title_search:
                qs = qs.filter(title__icontains=title_search)

        return qs.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "cinema_hall", "movie"
    ).prefetch_related("tickets")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        qs = self.queryset

        if self.action == "list":
            movie_param, date_search = self.request.query_params.get(
                "movie"
            ), self.request.query_params.get("date")
            if movie_param and movie_param.isdigit():
                movie_param = int(movie_param)
                qs = qs.filter(movie=movie_param)
            if date_search:
                qs = qs.filter(show_time__date=date_search)

            qs = qs.annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer
        return OrderCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
