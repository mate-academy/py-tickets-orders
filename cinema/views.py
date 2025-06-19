from datetime import datetime

from django.db.models import F, Count, ExpressionWrapper, IntegerField
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
    MovieListSerializer, OrderListSerializer, OrderSerializer
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()

        title_param = self.request.query_params.get("title")
        actors_param = self.request.query_params.get("actors")
        genres_param = self.request.query_params.get("genres")

        if title_param:
            queryset = queryset.filter(title__icontains=title_param)

        if actors_param:
            actors_param = self._params_to_ints(actors_param)
            queryset = queryset.filter(actors__id__in=actors_param)

        if genres_param:
            genres_param = self._params_to_ints(genres_param)
            queryset = queryset.filter(genres__id__in=genres_param)

        return queryset.prefetch_related("genres", "actors")


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = MovieSession.objects.all()

        date_param = self.request.query_params.get("date")
        movie_param = self.request.query_params.get("movie")

        if date_param and movie_param:
            date_param = datetime.strptime(date_param, "%Y-%m-%d").date()
            queryset = queryset.filter(
                show_time__date=date_param,
                movie__id=int(movie_param)
            )

        if date_param:
            queryset = queryset.filter(show_time__date=date_param)

        if movie_param:
            queryset = queryset.filter(movie__id=int(movie_param))

        queryset = (
            queryset
            .select_related("cinema_hall", "movie")
            .annotate(
                tickets_available=ExpressionWrapper(
                    (
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                    )
                    - Count("tickets"),
                    output_field=IntegerField()
                )
            )
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = Order.objects.all().filter(user=self.request.user)
        queryset = queryset.prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer_class = OrderListSerializer
        if self.action == "list":
            serializer_class = OrderListSerializer
            return serializer_class
        elif self.action == "create":
            serializer_class = OrderSerializer
            return serializer_class
        return serializer_class
