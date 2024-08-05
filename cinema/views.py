import datetime

from django.core.exceptions import ValidationError
from django.db.models import F, Count, Func
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
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__in=actors_ids)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__in=genres_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

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

    @staticmethod
    def _param_to_date(query_string):
        try:
            return datetime.datetime.strptime(query_string, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(
                "Invalid date format. Expected YYYY-MM-DD."
            )

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                            F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                            - Count("tickets")
                    )
                )
            )
        elif self.action == "retrieve":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .prefetch_related("tickets")
            )

        date = self.request.query_params.get("date")
        if date:
            try:
                date_obj = self._param_to_date(date)
                queryset = queryset.filter(show_time__date=date_obj)
            except ValueError:
                raise ValidationError("Invalid date format. Expected YYYY-MM-DD.")

        movie = self.request.query_params.get("movie")
        if movie:
            try:
                movie_id = int(movie)
                queryset = queryset.filter(movie_id=movie_id)
            except ValueError:
                raise ValidationError("Invalid movie ID format. Expected an integer.")

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session",
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
