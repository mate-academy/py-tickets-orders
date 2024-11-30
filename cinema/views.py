from datetime import datetime

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
    MovieListSerializer, OrderSerializer, OrderListSerializer,
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

    def get_serializer_class(self):
        if self.action == "list":
            return CinemaHallSerializer
        return CinemaHallSerializer


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
    def _params_to_ints(query_string):
        """Converts a string of format '1,2,3' to a list of [1,2,3]"""
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        queryset = self.queryset
        if actors:
            queryset = Movie.objects.filter(actors__id=actors)
        if title:
            queryset = Movie.objects.filter(title__icontains=title)
        if genres:
            genres = self._params_to_ints(genres)
            queryset = Movie.objects.filter(genres__id__in=genres)
        if self.action == ("list", "retrieve"):
            queryset = Movie.objects.prefetch_related("actors")
        return queryset.distinct()


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
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(
                show_time__year=date_obj.year,
                show_time__day=date_obj.day,
                show_time__month=date_obj.month
            )
        if movie:
            queryset = queryset.filter(movie_id=movie)
        if self.action == "list":
            queryset = queryset.select_related().prefetch_related("tickets")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "cinema_hall"
            ).select_related()
        return queryset


class OrderViewPaginator(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderViewPaginator

    def get_queryset(self):
        queryset = self.queryset.select_related().prefetch_related(
            "tickets__movie_session__movie"
        )
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.action == "list":
            serializer_class = OrderListSerializer
        return serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
