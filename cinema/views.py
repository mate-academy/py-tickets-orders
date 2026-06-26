from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    MovieSessionSerializer,
    OrderCreateSerializer,
    OrderSerializer,
)


def _parse_int_list(value):
    ids = []

    for item in value.split(","):
        if item.isdigit():
            ids.append(int(item))

    return ids


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
        queryset = self.queryset.all()

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            genre_ids = _parse_int_list(genres)

            if not genre_ids:
                return queryset.none()

            queryset = queryset.filter(genres__id__in=genre_ids)

        if actors:
            actor_ids = _parse_int_list(actors)

            if not actor_ids:
                return queryset.none()

            queryset = queryset.filter(actors__id__in=actor_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset.select_related("movie", "cinema_hall")
        params = self.request.query_params
        movie = params.get("movie")
        date = params.get("date")

        if self.action == "list":
            rows = F("cinema_hall__rows")
            seats_in_row = F("cinema_hall__seats_in_row")
            cinema_hall_capacity = rows * seats_in_row

            queryset = queryset.annotate(
                tickets_available=cinema_hall_capacity - Count("tickets")
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")

        if movie:
            movie_ids = _parse_int_list(movie)

            if not movie_ids:
                return queryset.none()

            queryset = queryset.filter(movie_id__in=movie_ids)

        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer

        return OrderSerializer
