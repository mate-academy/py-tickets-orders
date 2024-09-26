from django.db.models import Count, F
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


class ParamsToIntMixin:
    @staticmethod
    def _params_to_int(qs) -> list:
        return [int(str_id) for str_id in qs.split(",")]


class MovieViewSet(ParamsToIntMixin, viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("genres", "actors")
        actors = self.request.query_params.get("actors", "")
        genres = self.request.query_params.get("genres", "")
        title = self.request.query_params.get("title", "")

        if actors:
            actors_ids = self._params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = self._params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return self.serializer_class


class MovieSessionViewSet(ParamsToIntMixin, viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        date = self.request.query_params.get("date", "")
        movies = self.request.query_params.get("movie", "")

        if self.action == "list":
            queryset = (
                queryset.select_related("movie", "cinema_hall").annotate(
                    tickets_available=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            ).order_by("id")

        if movies:
            movies_ids = self._params_to_int(movies)
            queryset = self.queryset.filter(movie_id__in=movies_ids)

        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return self.serializer_class


class OrderPagination(PageNumberPagination):
    page_size = 5
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
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
