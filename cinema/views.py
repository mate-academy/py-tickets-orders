import datetime

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
    OrderListSerializer
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
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("actors", "genres")
        search_actors = self.request.query_params.get("actors")
        search_genres = self.request.query_params.get("genres")
        search_title = self.request.query_params.get("title")

        if search_actors:
            actors_ids = self._params_to_ints(search_actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if search_genres:
            genres_ids = self._params_to_ints(search_genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if search_title:
            queryset = queryset.filter(title__icontains=search_title)

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
        search_movie = self.request.query_params.get("movie")
        search_date = self.request.query_params.get("date")

        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .annotate(
                    tickets_available=F(
                        "cinema_hall__rows") * F(
                        "cinema_hall__seats_in_row"
                    ) - Count("tickets")
                )
            ).order_by("id")

        if search_movie:
            movie_id = int(search_movie)
            queryset = queryset.filter(movie__id=movie_id)

        if search_date:
            session_date = datetime.datetime.strptime(search_date, "%Y-%m-%d")
            queryset = queryset.filter(show_time__day=session_date.day)

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related("tickets")
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
