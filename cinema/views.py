from django.db.models import F, Count
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

        return MovieSerializer

    @staticmethod
    def _param_to_int(query):
        return [int(str_id) for str_id in query.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actor_id = self._param_to_int(actors)
            queryset = queryset.filter(actors__id__in=actor_id)

        if genres:
            genre_id = self._param_to_int(genres)
            queryset = queryset.filter(genres__id__in=genre_id)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("retrieve", "list"):
            queryset = queryset.prefetch_related("genres", "actors")

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

    @staticmethod
    def _param_id(query):
        return [int(_id) for _id in query.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        date = self.request.query_params.get("date")
        movies = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movies:
            movie_id = self._param_id(movies)
            queryset = queryset.filter(movie__id__in=movie_id)

        if self.action == "list":
            queryset = (
                queryset.select_related("movie", "cinema_hall").annotate(
                    tickets_available=(F
                                       ("cinema_hall__seats_in_row")
                                       * F("cinema_hall__rows")
                                       - Count("tickets")
                                       )
                )
            )

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
