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
    MovieListSerializer, TicketSerializer, OrderCreateSerializer, OrderSerializer,
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
    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("genres", "actors")
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            queryset = queryset.filter(actors__id=actors)
        if genres:
            queryset = queryset.filter(genres__id=genres)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie",
        "cinema_hall",
    ).prefetch_related(
        "movie__genres",
        "movie__actors",
        "tickets",
    )
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.select_related(
            "movie",
            "cinema_hall",
        ).prefetch_related(
            "movie__genres",
            "movie__actors",
            "tickets",
        )
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=movie)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

class TicketsViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )
    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer