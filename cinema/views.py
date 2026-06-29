from django.db.models import Count, F

from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    MovieSessionSerializer,
    OrderListSerializer,
    OrderSerializer,
)


def _params_to_ints(query_string):
    return [int(str_id) for str_id in query_string.split(",")]


class OrderPagination(PageNumberPagination):
    page_size = 10


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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genres_ids = _params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if actors:
            actors_ids = _params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie",
        "cinema_hall",
    )
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)

        if movie:
            queryset = queryset.filter(movie_id=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall",
    )
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
