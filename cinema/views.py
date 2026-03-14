from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

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
    MovieListSerializer,
    MovieDetailSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by("id")
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all().order_by("id")
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all().order_by("id")
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("genres", "actors")

        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            ids = [int(pk) for pk in genres.split(",") if pk.isdigit()]
            if ids:
                queryset = queryset.filter(genres__id__in=ids)
            else:
                return Movie.objects.none()

        if actors:
            ids = [int(pk) for pk in actors.split(",") if pk.isdigit()]
            if ids:
                queryset = queryset.filter(actors__id__in=ids)
            else:
                return Movie.objects.none()

        return queryset.distinct().order_by("id")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all().order_by("id")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = (
            MovieSession.objects
            .select_related("movie", "cinema_hall")
            .prefetch_related(
                "movie__genres",
                "movie__actors",
                "tickets",
            )
        )

        movie_id = self.request.query_params.get("movie")
        if movie_id:
            if movie_id.isdigit():
                queryset = queryset.filter(movie_id=int(movie_id))
            else:
                return MovieSession.objects.none()

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset.order_by("id")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return (
            qs.filter(user=self.request.user)
            .prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderSerializer
        return OrderCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
