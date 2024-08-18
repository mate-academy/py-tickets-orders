from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from django.db.models import F, Count

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
    OrderListSerializer,
    OrderSerializer,
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

    def _params_to_int(self, params: str) -> list[int]:
        return [int(str_id) for str_id in params.split(",")]

    def _filter_by_actors(self, queryset):
        actors = self.request.query_params.get("actors", )
        if actors:
            actor_ids = self._params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)
        return queryset

    def _filter_by_genres(self, queryset):
        genres = self.request.query_params.get("genres", )
        if genres:
            genre_ids = self._params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)
        return queryset

    def _filter_by_movie_title(self, queryset):
        title = self.request.query_params.get("title", )
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset

    def _filter_queryset(self, queryset):
        queryset = self._filter_by_actors(queryset)
        queryset = self._filter_by_genres(queryset)
        queryset = self._filter_by_movie_title(queryset)
        return queryset.distinct()

    def get_queryset(self):
        self.queryset = self._filter_queryset(self.queryset)

        if self.action in ("list", "retrieve", ):
            return self.queryset.prefetch_related("genres", "actors", )
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def _filter_by_date(self, queryset):
        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)
        return queryset

    def _filter_by_movie(self, queryset):
        movie = self.request.query_params.get("movie")
        if movie:
            movie_ids = [int(str_id) for str_id in movie.split(",")]
            queryset = queryset.filter(movie__id__in=movie_ids)
        return queryset

    def _filter_queryset(self, queryset):
        queryset = self._filter_by_date(queryset)
        queryset = self._filter_by_movie(queryset)
        return queryset.distinct()

    def get_queryset(self):
        self.queryset = self._filter_queryset(self.queryset)

        if self.action == "list":
            self.queryset = self.queryset.select_related(
                "movie", "cinema_hall",
            ).annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                ) - Count("tickets")
            )
        elif self.action == "retrieve":
            return self.queryset.select_related("movie", "cinema_hall")

        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 1000


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            return self.queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie",
            )
        return queryset.prefetch_related("tickets")

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
