from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

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
        queryset = Movie.objects.all()

        title = self.request.query_params.get("title", None)
        if title is not None:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres", None)
        if genres is not None:
            try:
                # Handle comma-separated IDs
                if "," in genres:
                    genre_ids = [int(g) for g in genres.split(",")]
                    queryset = queryset.filter(genres__id__in=genre_ids)
                else:
                    genre_id = int(genres)
                    queryset = queryset.filter(genres__id=genre_id)
            except ValueError:
                queryset = queryset.filter(genres__name__icontains=genres)

        actors = self.request.query_params.get("actors", None)
        if actors is not None:
            try:
                actor_id = int(actors)
                queryset = queryset.filter(actors__id=actor_id)
            except ValueError:
                queryset = queryset.filter(
                    Q(actors__first_name__icontains=actors)
                    | Q(actors__last_name__icontains=actors)
                )

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
        queryset = MovieSession.objects.all()

        date = self.request.query_params.get("date", None)
        if date is not None:
            queryset = queryset.filter(show_time__date=date)

        movie = self.request.query_params.get("movie", None)
        if movie is not None:
            queryset = queryset.filter(movie__id=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
