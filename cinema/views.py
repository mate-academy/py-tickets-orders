from rest_framework import viewsets
from django.db.models import Count, F
from django.db.models.functions import Coalesce

from cinema.models import (
    Genre, Actor, Movie, Order,
    MovieSession, Ticket, CinemaHall,
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
    TicketSerializer,
    OrderSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
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

    def get_queryset(self):
        queryset = self.queryset

        title = self.request.query_params.get("title")
        genres = self.request.query_params.getlist("genres")
        actors = self.request.query_params.getlist("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres:
            clean_genres = []
            for genre in genres:
                clean_genres.extend(genre.split(","))

            if clean_genres[0].isdigit():
                queryset = queryset.filter(
                    genres__id__in=clean_genres
                ).distinct()
            else:
                queryset = queryset.filter(
                    genres__name__in=clean_genres
                ).distinct()
        if actors:
            clean_actors = []
            for actor in actors:
                clean_actors.extend(actor.split(","))

            if clean_actors[0].isdigit():
                queryset = queryset.filter(
                    actors__id__in=clean_actors
                ).distinct()
            else:
                queryset = queryset.filter(
                    actors__name__in=clean_actors
                ).distinct()
        return queryset


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

        if self.action in ("list", "retrieve"):
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .prefetch_related("tickets")
            )

        queryset = queryset.annotate(
            tickets_sold=Coalesce(Count("tickets"), 0),
            total_capacity=F("cinema_hall__rows") * F(
                "cinema_hall__seats_in_row"
            ),
            tickets_available=F("total_capacity") - F("tickets_sold")
        )

        date = self.request.query_params.get("date")

        movie_id = (
            self.request.query_params.get("movie")
            or self.request.query_params.get("movie_id")
        )

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            return self.queryset.filter(user=user)

        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
