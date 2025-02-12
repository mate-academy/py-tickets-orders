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
    Order,
    Ticket
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors_filter = self.request.query_params.get("actors")
        genres_filter = self.request.query_params.get("genres")
        title_filter = self.request.query_params.get("title")

        if actors_filter:
            actors_ids = [
                int(actor_id) for actor_id in actors_filter.split(",")
            ]
            queryset = queryset.filter(actors__in=actors_ids)
        if genres_filter:
            genres_ids = [
                int(genre_id) for genre_id in genres_filter.split(",")
            ]
            queryset = queryset.filter(genres__in=genres_ids)
        if title_filter:
            queryset = queryset.filter(title__icontains=title_filter)

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

        date = self.request.query_params.get("date")
        movie_to_find = self.request.query_params.get("movie")
        if movie_to_find:
            queryset = queryset.filter(movie_id=int(movie_to_find))

        if date:
            date_list = date.split("-")
            format_date = datetime.datetime(
                year=int(date_list[0]),
                month=int(date_list[1]),
                day=int(date_list[2])
            )
            queryset = queryset.filter(
                show_time__year=format_date.year,
                show_time__month=format_date.month,
                show_time__day=format_date.day
            )

        if self.action == "list":
            queryset = queryset.select_related("cinema_hall").annotate(
                tickets_available=F(
                    "cinema_hall__rows"
                ) * F(
                    "cinema_hall__seats_in_row"
                ) - Count("tickets")
            )

        return queryset.select_related("movie", "cinema_hall")


class OrderSetPagination(PageNumberPagination):
    page_size = 2
    page_query_param = "page"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset
        return queryset.prefetch_related(
            "tickets__movie_session",
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        ).filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
