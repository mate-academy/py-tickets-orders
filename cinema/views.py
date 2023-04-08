from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order
)

from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    OrderSerializer,

    MovieListSerializer,
    OrderListSerializer,
    MovieSessionListSerializer,

    MovieDetailSerializer,
    MovieSessionDetailSerializer,
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_ints(qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            actors_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__in=actors_ids)
        if genres:
            genres_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__in=genres_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie=movie)

        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        return queryset.order_by("show_time")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__cinema_hall",
        "tickets__movie_session__movie"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
