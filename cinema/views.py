from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (Genre, Actor, CinemaHall,
                           Movie, MovieSession, Order)

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


class MovieViewSet(viewsets.ModelViewSet):
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
        queryset = queryset.prefetch_related("actors", "genres")
        if self.action == "list":
            actors = self.request.query_params.get("actors")
            if actors:
                actors_ids = [int(actor_id) for actor_id in actors.split(",")]
                queryset = queryset.filter(actors__id__in=actors_ids)

            genres = self.request.query_params.get("genres")
            if genres:
                genres_ids = [int(genres_id) for genres_id
                              in genres.split(",")]
                queryset = queryset.filter(genres__id__in=genres_ids)

            title = self.request.query_params.get("title")
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
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets", "cinema_hall",
                                                 "movie").annotate(
                tickets_available=(F("cinema_hall__rows")
                                   * F("cinema_hall__seats_in_row")
                                   - Count("tickets")))
            date_stamp = self.request.query_params.get("date")
            if date_stamp:
                date_stamp = date_stamp.split("-")
                year, month, day = [int(date) for date in date_stamp]
                queryset = queryset.filter(show_time__year=year,
                                           show_time__month=month,
                                           show_time__day=day)

            movie = self.request.query_params.get("movie")
            if movie:
                queryset = queryset.filter(movie__id=int(movie))

        return queryset


class OrderResultsSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 1000


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderResultsSetPagination

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
