import datetime

from django.db.models import F, Count
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
    OrderSerializer,
    OrderListSerializer,
    OrderCreateSerializer,

)


def get_indexes(params: str):
    return [int(str_id) for str_id in params.split(",")]


class OrderPagination(PageNumberPagination):
    page_size = 10
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

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            try:
                actors_ids = get_indexes(actors)
            except ValueError:
                pass
                # return rest_framework.exceptions.bad_request(request=self.request, exception=ValueError)
                # HOW TO HANDLE IT????
            queryset = queryset.filter(actors__id__in=actors_ids)
        if genres:
            try:
                genre_ids = [int(str_id) for str_id in genres.split(",")]
            except ValueError:
                pass
            queryset = queryset.filter(genres__id__in=genre_ids)

        return queryset.distinct().prefetch_related("genres").prefetch_related("actors")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


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

        if self.action != "list":
            return queryset.distinct()

        movie_id = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)
        if date:
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d")
            except AttributeError:
                pass
            # How to handle???

            queryset = queryset.filter(
                show_time__year=date.year,
                show_time__day=date.day,
                show_time__month=date.month,
            )
        return queryset.distinct().annotate(
            tickets_available=(F("cinema_hall__rows") * F("cinema_hall__seats_in_row")) - Count(
                "tickets")).select_related("cinema_hall").select_related("movie")




class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.filter(user=self.request.user).prefetch_related(
                "tickets__movie_session__movie"
            ).prefetch_related("tickets__movie_session__cinema_hall")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
