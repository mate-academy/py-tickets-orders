from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket

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
    OrderPostSerializer,
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

        genres = self.request.query_params.get("genres")
        if genres:
            genre_ids = genres.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids)

        actors = self.request.query_params.get("actors")
        if actors:
            actor_ids = actors.split(",")
            queryset = queryset.filter(actors__id__in=actor_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


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
        queryset = self.queryset

        data = self.request.query_params.get("data")
        if data:
            queryset = queryset.filter(show_time=data)

        movie = self.request.query_params.get("movie")
        if movie:
            movie_ids = movie.split(",")
            queryset = queryset.filter(movie__id__in=movie_ids)

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("movie", "cinema_hall")
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return OrderSerializer
        return OrderPostSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
