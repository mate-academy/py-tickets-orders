from datetime import datetime

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

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
    OrderDetailSerializer,
)


class OrderResultsSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 1


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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors:
            actors_id = [int(pk) for pk in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_id)
        if genres:
            genres_id = [int(pk) for pk in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_id)
        if title:
            queryset = queryset.filter(title__icontains=title)
        if self.action == "list":
            return (
                queryset.prefetch_related("genres", "actors")
                .distinct()
            )
        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            try:
                date_str = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date_str)
            except ValueError:
                pass
        if movie:
            movie_id = int(movie)
            queryset = queryset.filter(movie=movie_id)

        if self.action == "list":
            queryset = (
                queryset.select_related("cinema_hall", "movie")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__seats_in_row") * F("cinema_hall__rows")
                    ) - Count("tickets", distinct=True)
                )
            )
        elif self.action == "retrieve":
            queryset = (
                queryset.select_related("cinema_hall", "movie")
                .prefetch_related("tickets")
            )
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
    pagination_class = OrderResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderDetailSerializer
        return OrderSerializer
