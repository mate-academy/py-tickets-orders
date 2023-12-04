from django.db.models import F, Count
from datetime import datetime
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (Genre,
                           Actor,
                           CinemaHall,
                           Movie,
                           MovieSession,
                           Order)

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
    OrderListSerializer
)


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 50


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
    def _params_to_ints(query_params):
        return [int(str_id) for str_id in query_params.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_id = self._params_to_ints(actors)
            queryset = queryset.filter(actors__in=actors_id)

        if genres:
            genres_id = self._params_to_ints(genres)
            queryset = queryset.filter(genres__in=genres_id)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


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
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related(
                "cinema_hall",
                "movie"
            ).annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )

        date_param = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date_param:
            date = datetime.strptime(date_param, "%Y-%m-%d").date()

            queryset = queryset.filter(
                show_time__date=date
            )

        if movie_id:
            queryset = queryset.filter(
                movie__pk=movie_id
            )

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user.id)
        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
