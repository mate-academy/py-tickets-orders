from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_int(qs):
        return [int(params) for params in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        if actors:
            actors_list = self._params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actors_list)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_list = self._params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genres_list)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    @staticmethod
    def _make_date_valid(date_non_valid):
        parts_of_date = date_non_valid.split("-")
        if len(parts_of_date[1]) == 1:
            parts_of_date[1] = "0" + parts_of_date[1]
        if len(parts_of_date[2]) == 1:
            parts_of_date[2] = "0" + parts_of_date[2]

        return "-".join(parts_of_date)

    @staticmethod
    def _qs_to_list_int(qs):
        return [int(current_id) for current_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset.annotate(
            tickets_available=F("cinema_hall__rows")
            * F("cinema_hall__seats_in_row")
            - Count("tickets")
        )

        movies = self.request.query_params.get("movie")
        if movies:
            movie_list = self._qs_to_list_int(movies)
            queryset = queryset.filter(movie__id__in=movie_list)

        date = self.request.query_params.get("date")
        if date:
            # Tests are failed because date in tests in format (2024-03-4),
            # not (2024-03-04), so i make validation
            date = self._make_date_valid(date)
            queryset = queryset.filter(show_time__contains=date)
        return queryset


class OrderPaggination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page-size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPaggination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
