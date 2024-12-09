from django.db.models import Count, F
from django.db.models import annotate
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
    MovieListSerializer, OrderSerializer,
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
        actor_names = self.request.query_params.get("actor")
        genre_names = self.request.query_params.get("genre")
        title = self.request.query_params.get("title")
        if actor_names:
            actor_list = actor_names.split(",")
            queryset = queryset.filter(actors__last_name__in=actor_list)
        if genre_names:
            genre_list = genre_names.split(",")
            queryset = queryset.filter(genres__in=genre_list)
        if title:
            queryset = queryset.filter(title__icontains=title)
        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("genres", "actors")
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
        queryset = self.queryset
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            queryset = queryset.filter(show_time__contains=date)
        if movie:
            queryset = queryset.filter(movie=movie)
        if self.action == "list":
            queryset = ((
                        queryset
                        .prefetch_related("genres", "actors"))
                        .annotate(tickets_available=F(
                            "cinema_hall__capacity")
                            - Count("tickets"))
                        ).order_by("id")
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

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
