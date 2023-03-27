from django.db.models import Count, F
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
    OrderSerializer, OrderPostSerializer,
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
    def str_to_int(attrs):
        return [int(attr) for attr in attrs.split(",")]

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("actors", "genres")
        get_attrs = self.request.query_params.get

        title = get_attrs("title")
        actors = self.str_to_int(get_attrs("actors")) if get_attrs("actors") else None
        genres = self.str_to_int(get_attrs("genres")) if get_attrs("genres") else None
        for attr, name in [
            [title, "title__contains"],
            [actors, "actors__id__in"],
            [genres, "genres__id__in"]
        ]:
            if attr:
                queryset = queryset.filter(**{name: attr})
        return queryset

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
        queryset = self.queryset.prefetch_related("movie", "cinema_hall")
        get_attrs = self.request.query_params.get

        movie = get_attrs("movie")
        date = get_attrs("date").strftime("%Y %m %d")
        for attr, name in [
            [movie, "movie__id"],
            [date, "show_time__contains"]
        ]:
            if attr:
                queryset = queryset.filter(**{name: attr})
        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderPostSerializer

        return OrderSerializer
