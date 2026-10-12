from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from cinema.pagination import OrderPagination

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
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    MovieSessionWriteSerializer,
    MovieWriteSerializer,
    OrderListSerializer,
    OrderSerializer,
)


def parse_ids(value):
    if not value:
        return []

    try:
        return [int(item.strip()) for item in value.split(",")]
    except ValueError:
        return []


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
    queryset = Movie.objects.prefetch_related("genres", "actors")

    def get_queryset(self):
        queryset = self.queryset
        params = self.request.query_params

        actor_ids = parse_ids(params.get("actors"))
        genre_ids = parse_ids(params.get("genres"))
        title = params.get("title")

        if actor_ids:
            queryset = queryset.filter(actors__id__in=actor_ids)

        if genre_ids:
            queryset = queryset.filter(genres__id__in=genre_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieWriteSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie",
        "cinema_hall",
    ).prefetch_related(
        "movie__genres",
        "movie__actors",
    )

    def get_queryset(self):
        queryset = self.queryset
        params = self.request.query_params

        date = params.get("date")
        movie_id = params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie_id:
            if movie_id.isdigit():
                queryset = queryset.filter(movie_id=int(movie_id))
            else:
                queryset = queryset.none()

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets", distinct=True)
                ),
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionWriteSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie__genres",
                "tickets__movie_session__movie__actors",
                "tickets__movie_session__cinema_hall",
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
