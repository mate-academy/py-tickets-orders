from django.db.models import ExpressionWrapper, Count, F, IntegerField
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
    MovieListSerializer, OrderListSerializer, OrderCreateSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = "page_size"
    max_page_size = 100


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
        queryset = super().get_queryset().prefetch_related("genres", "actors")

        if self.action == "list":
            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            title = self.request.query_params.get("title")
            if actors:
                actors_id = [int(id_) for id_ in actors.split(",")]
                queryset = queryset.filter(actors__id__in=actors_id)
            if genres:
                genres_id = [int(id_) for id_ in genres.split(",")]
                queryset = queryset.filter(genres__id__in=genres_id)
            if title:
                queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


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
        queryset = (
            super().get_queryset()
            .select_related("movie", "cinema_hall")
            .annotate(
                tickets_sold=Count("tickets"),
                tickets_available=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - F("tickets_sold"),
                    output_field=IntegerField()
                )
            )
        )

        if self.action == "list":
            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            if date:
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.filter(movie__id=movie)

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "create":
            return OrderCreateSerializer

    def get_queryset(self):
        if self.action == "list":
            return (
                self.queryset.filter(user=self.request.user)
                .prefetch_related(
                    "tickets__movie_session__movie",
                    "tickets__movie_session__cinema_hall"
                )
            )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
