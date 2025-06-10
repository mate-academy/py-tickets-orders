from django.db.models import Count, F, IntegerField, ExpressionWrapper
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
    MovieListSerializer, OrderSerializer, OrderCreateSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = "page_size"
    max_page_size = 100


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
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")

        if self.request.method == "GET":
            if actors:
                actors = self._params_to_ints(actors)
                queryset = queryset.filter(actors__id__in=actors)
            if genres:
                genres = self._params_to_ints(genres)
                queryset = queryset.filter(genres__id__in=genres)
            if title:
                queryset = queryset.filter(title__icontains=title)

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
        queryset = (
            super().get_queryset()
            .select_related("movie", "cinema_hall")
            .annotate(
                tickets_sold=Count("tickets"),
                tickets_available=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - F("tickets_sold"),
                    output_field=IntegerField()
                )
            )
        )

        if self.action == "list":
            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            if date:
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.filter(movie__id=movie)

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderSerializer
        elif self.action == "create":
            serializer = OrderCreateSerializer
        return serializer
