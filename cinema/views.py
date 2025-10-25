from rest_framework import (
    viewsets,
    permissions,
    filters
)

from django_filters.rest_framework import DjangoFilterBackend
from django.utils.dateparse import parse_date

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
    OrderListSerializer,
    OrderCreateSerializer
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


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors").all()
    serializer_class = MovieListSerializer
    filter_backends = [DjangoFilterBackend]

    filterset_fields = {
        "genres": ["exact"],
        "actors": ["exact"],
        "title": ["icontains"]
    }

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieListSerializer


class MovieSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall").all()
    serializer_class = MovieSessionListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_str = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(show_time__date=date)

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionListSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
            .order_by("id")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
