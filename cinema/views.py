from datetime import datetime, time

from django.db.models import (
    F,
    Count,
    ExpressionWrapper,
    IntegerField
)
from django.utils.dateparse import parse_date
from rest_framework import viewsets

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("actors", "genres")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = [int(actor_id) for actor_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)
        if genres:
            genres_ids = [int(genre_id) for genre_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)
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
    pagination_class = None

    def get_queryset(self):
        queryset = MovieSession.objects.all()

        date = self.request.query_params.get("date")
        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                queryset = queryset.filter(show_time__date=parsed_date)

        movie_param = self.request.query_params.get("movie")
        if movie_param:
            movie_ids = [int(m_id) for m_id in movie_param.split(",")]
            queryset = queryset.filter(movie__id__in=movie_ids)

        total_seats = F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
        tickets_sold = Count("tickets", distinct=True)

        queryset = (
            queryset
            .select_related("movie", "cinema_hall")
            .annotate(
                tickets_available=ExpressionWrapper(
                    total_seats - tickets_sold,
                    output_field=IntegerField()
                )
            )
            .order_by("id")
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                "tickets",
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
