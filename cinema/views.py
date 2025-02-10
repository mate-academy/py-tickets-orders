from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    OrderListSerializer,
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title", None)
        genres = self.request.query_params.get("genres", None)
        actors = self.request.query_params.get("actors", None)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genre_ids = genres.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids).distinct()

        if actors:
            actor_ids = actors.split(",")
            queryset = queryset.filter(actors__id__in=actor_ids).distinct()

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset
        date = self.request.query_params.get("date", None)
        movie_id = self.request.query_params.get("movie", None)

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie_id:
            queryset = queryset.filter(movie__id=movie_id)

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = (
            self.queryset
            .prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )
        )
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = OrderListSerializer
        return serializer
