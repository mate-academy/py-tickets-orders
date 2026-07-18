from django.db.models import QuerySet
from rest_framework import viewsets, pagination
from rest_framework.exceptions import NotAuthenticated

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

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres:
            genre_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genre_ids)
        if actors:
            actor_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actor_ids)
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

    def get_queryset(self):
        queryset = self.queryset.prefetch_related(
            "tickets",
            "cinema_hall",
            "movie"
        )
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie:
            queryset = queryset.filter(movie_id=int(movie))
        if date:
            queryset = queryset.filter(show_time__date=date)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(pagination.PageNumberPagination):
    page_size = 1


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet | None:
        if self.request.user.is_authenticated:
            return (self.queryset.filter(user=self.request.user).
                    prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
            )

    def perform_create(self, serializer) -> None:
        if not self.request.user.is_authenticated:
            raise NotAuthenticated("Login to create order!")
        serializer.save(user=self.request.user)
