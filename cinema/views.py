from django.db.models import F, Count
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

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
    OrderSerializer, OrderListSerializer,
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
    def params_to_ints(query_strings):
        """Convert a list of string IDs to a list of integers."""
        try:
            result = [
                int(str_id)
                for str_id in query_strings.split(",")
                if str_id.isdigit()
            ]
        except ValueError:
            result = []
        return result

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()

        title = self.request.query_params.get("title", None)
        if title:
            queryset = queryset.filter(title__icontains=title)
        actors = self.request.query_params.get("actors", None)
        if actors:
            actors = self.params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors)
        genres = self.request.query_params.get("genres", None)
        if genres:
            genres = self.params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres)

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

        date_str = self.request.query_params.get("date", None)
        if date_str:
            data = parse_date(date_str)
            if data:
                queryset = queryset.filter(show_time__date=data)
        movie_id = self.request.query_params.get("movie", None)
        if movie_id:
            queryset = queryset.filter(movie_id=int(movie_id))

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")
        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .prefetch_related("tickets")
                .annotate(
                    tickets_available=F(
                        "cinema_hall__capacity"
                    ) - Count("tickets")
                )
            )

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = OrderListSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__movie_session")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
