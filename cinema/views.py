from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer

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
    OrderDetailSerializer,
    OrderSerializer
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[Movie]:
        queryset = super().get_queryset()
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genre_ids = [int(g) for g in genres.split(",") if g.isdigit()]
            queryset = queryset.filter(genres__id__in=genre_ids)

        if actors:
            actor_ids = [int(a) for a in actors.split(",") if a.isdigit()]
            queryset = queryset.filter(actors__id__in=actor_ids)

        return queryset.distinct()

    def get_serializer_class(self) -> type[ModelSerializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[MovieSession]:
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=movie)

        return queryset

    def get_serializer_class(self) -> type:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        )

    def get_serializer_class(self) -> type:
        if self.action in ["list", "retrieve"]:
            return OrderDetailSerializer
        return OrderSerializer
