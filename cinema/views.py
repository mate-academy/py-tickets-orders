from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
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
    OrderListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = OrderPagination
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.prefetch_related("tickets").filter(
            user=self.request.user
        )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all().order_by("id")
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related(
            "genres", "actors"
        )

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            genre_ids = [
                int(genre) for genre in genres.split(",") if genre.isdigit()
            ]
            if genre_ids:
                queryset = queryset.filter(
                    genres__id__in=genre_ids
                ).distinct()

        if actors:
            actor_ids = [
                int(a) for a in actors.split(",") if a.isdigit()
            ]
            if actor_ids:
                queryset = queryset.filter(
                    actors__id__in=actor_ids
                ).distinct()

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all().order_by("id")
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.select_related(
            "movie", "cinema_hall"
        )

        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date:
            try:
                date_obj = datetime.strptime(
                    date, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(show_time__date=date_obj)
            except ValueError:
                pass

        if movie_id and movie_id.isdigit():
            queryset = queryset.filter(movie_id=movie_id)

        return queryset
