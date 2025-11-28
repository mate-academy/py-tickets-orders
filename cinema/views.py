from django.db.models import Prefetch, Count
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def params_to_ints(query_str):
        return [int(str_id) for str_id in query_str.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        actors_data = self.request.query_params.get("actors")
        genres_data = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors_data:
            actors = self.params_to_ints(actors_data)
            queryset = queryset.filter(actors__id__in=actors)
        if genres_data:
            genres = self.params_to_ints(genres_data)
            queryset = queryset.filter(genres__id__in=genres)
        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action == "list":
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=movie)

        if self.action == "list":
            queryset = queryset.select_related(
                "cinema_hall",
                "movie",
            ).annotate(
                tickets_sold=Count("tickets")
            )
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            optimized_sessions = MovieSession.objects.select_related(
                "movie",
                "cinema_hall"
            ).annotate(
                tickets_sold=Count("tickets")
            )

            queryset = queryset.prefetch_related(
                Prefetch(
                    "tickets__movie_session",
                    queryset=optimized_sessions
                ),
                "tickets"
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
