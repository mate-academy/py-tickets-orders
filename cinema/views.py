from django.db.models import Count, IntegerField, Prefetch
from django.db.models.expressions import F, ExpressionWrapper
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    OrdersSerializer,
)


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrdersSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors_param = self.request.query_params.get("actors")
        genres_param = self.request.query_params.get("genres")
        title_param = self.request.query_params.get("title")

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        if actors_param:
            actor_ids = [
                int(x.strip()) for x in actors_param.split(",")
                if x.strip().isdigit()
            ]
            queryset = queryset.filter(actors__in=actor_ids)

        if genres_param:
            genre_ids = [
                int(x.strip()) for x in genres_param.split(",")
                if x.strip().isdigit()
            ]
            queryset = queryset.filter(genres__in=genre_ids)

        if title_param:
            queryset = queryset.filter(title__icontains=title_param)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        date_param = self.request.query_params.get("date")
        movie_param = self.request.query_params.get("movie")

        if date_param:
            queryset = queryset.filter(show_time__date=date_param)

        if movie_param:
            queryset = queryset.filter(movie=movie_param)

        if self.action == "list":
            database_capacity = ExpressionWrapper(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row"),
                output_field=IntegerField()
            )

            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .annotate(
                    cinema_hall_capacity=database_capacity,
                    tickets_available=database_capacity - Count("tickets")
                )
            )

        if self.action == "retrieve":
            queryset = queryset.select_related()

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer
