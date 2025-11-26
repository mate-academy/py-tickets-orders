from rest_framework import viewsets
from rest_framework.request import Request
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from rest_framework.permissions import IsAuthenticated
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
        queryset = super().get_queryset()
        actors = self.request.GET.get("actors")
        genres = self.request.GET.get("genres")
        title = self.request.GET.get("title")

        if actors is not None:
            actors_list = actors.split(',')
            queryset = queryset.filter(actors__id__in=actors_list)

        if genres is not None:
            genres_list = genres.split(',')
            queryset = queryset.filter(genres__id__in=genres_list)

        if title is not None:
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

    def get_queryset(self):
        queryset = super().get_queryset()
        movie = self.request.GET.get("movie")
        date = self.request.GET.get("date")

        if movie is not None:
            movie_list = movie.split(',')
            queryset = queryset.filter(movie__id__in=movie_list)

        if date is not None:
            queryset = queryset.filter(show_time__date=date)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer

        return OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
