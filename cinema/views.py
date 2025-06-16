from datetime import datetime

from django.db.models import F, Q
from django.db.models.aggregates import Count
from rest_framework import viewsets

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
    OrderDetailSerializer,
)
from cinema.utility import ids_str_to_int


class BaseViewSet(viewsets.ModelViewSet):
    pagination_class = None


class GenreViewSet(BaseViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(BaseViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(BaseViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(BaseViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        filters = Q()

        if genres:
            filters &= Q(genres__id__in=ids_str_to_int(genres))
        if actors:
            filters &= Q(actors__id__in=ids_str_to_int(actors))
        if title:
            filters &= Q(title__contains=title)

        queryset = queryset.filter(filters)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset.distinct()


class MovieSessionViewSet(BaseViewSet):
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

        date_str = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        filters = Q()

        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            filters &= Q(show_time__date=date_obj)

        if movie_id:
            filters &= Q(movie_id=movie_id)

        queryset = queryset.filter(filters)

        if self.action == "list":
            cinema_hall_capacity = F("cinema_hall__rows") * F(
                "cinema_hall__seats_in_row"
            )
            queryset = (queryset.select_related(
                "movie", "cinema_hall"
            ).annotate(
                tickets_available=cinema_hall_capacity - Count("tickets")
            ))

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user.id)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer
