from django.db.models import Count, F
from rest_framework import viewsets

from cinema.models import (Genre,
                           Actor,
                           CinemaHall,
                           Movie,
                           MovieSession,
                           Order)

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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("genres", "actors")

        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if actors:
            actor_ids = actors.split(",")
            queryset = queryset.filter(actors__id__in=actor_ids)

        if genres:
            genre_ids = genres.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie",
        "cinema_hall"
    ).prefetch_related(
        "tickets"
    )
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        if self.action == "retrieve":
            queryset = MovieSession.objects.select_related(
                "movie",
                "cinema_hall"
            ).prefetch_related("tickets")
            return queryset.distinct()

        if self.action == "list":
            queryset = MovieSession.objects.select_related(
                "movie",
                "cinema_hall"
            ).prefetch_related("tickets")

            queryset = queryset.annotate(
                taken=Count("tickets"),
                available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                ) - Count("tickets")
            )

            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")

            if date:
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.filter(movie__id=movie)

            return queryset.distinct()

        return self.queryset


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_queryset(self):
        qs = Order.objects.filter(user=self.request.user)
        if self.action == "list":
            qs = qs.select_related("user").prefetch_related("tickets")
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
