import datetime

from django.db.models import F, Count
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


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_ints(qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("actors", "genres")

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        actors = self.request.query_params.get("actors")
        if actors:
            actors_id = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_id)

        # actors = self.request.query_params.get("actors")
        # if actors:
        #     queryset = queryset.annotate(
        #         full_name=Concat(
        #             F("actors__first_name"),
        #             Value(" "),
        #             F("actors__last_name"),
        #             output_field=CharField(),
        #         )
        #     ).filter(full_name__icontains=actors)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_id = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_id)

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
        queryset = self.queryset.prefetch_related(
            "movie__genres", "movie__actors", "cinema_hall", "tickets"
        )

        show_time = self.request.query_params.get("date")
        if show_time:
            queryset = queryset.filter(
                show_time__date=datetime.datetime.strptime(
                    show_time,
                    "%Y-%m-%d"
                )
            )

        movie = self.request.query_params.get("movie")
        if movie:
            movie_id = MovieViewSet._params_to_ints(movie)
            queryset = queryset.filter(movie__id__in=movie_id)

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        queryset = queryset.prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
