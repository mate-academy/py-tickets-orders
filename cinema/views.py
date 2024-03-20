from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
)
from .serializers import (
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

    @staticmethod
    def _params_to_ints(qs: str) -> list:
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.prefetch_related("actors", "genres")

            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            title = self.request.query_params.get("title")

            if actors:
                actors_ids = self._params_to_ints(actors)
                queryset = queryset.filter(actors__id__in=actors_ids)

            if genres:
                genres_ids = self._params_to_ints(genres)
                queryset = queryset.filter(genres__id__in=genres_ids)

            if title:
                queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        MovieSession.objects.all()
        .select_related("movie", "cinema_hall")
        .annotate(tickets_available=(
            F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row")
            - Count("tickets"))
        )
    )
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = self.queryset

            date = self.request.query_params.get("date")
            movie_id = self.request.query_params.get("movie")

            if date:
                queryset = queryset.filter(show_time__date=date)

            if movie_id:
                queryset = queryset.filter(movie_id=movie_id)

        return queryset.distinct()


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
