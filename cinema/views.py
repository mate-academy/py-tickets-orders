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
    OrderSerializer,
    OrderListSerializer)


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

    @staticmethod
    def id_prepare(list_s):
        return [int(nums) for nums in list_s.split(",")]

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        if actors:
            self.queryset = self.queryset.filter(
                actors__id__in=self.id_prepare(actors))

        genres = self.request.query_params.get("genres")
        if genres:
            self.queryset = self.queryset.filter(
                genres__id__in=self.id_prepare(genres))

        title = self.request.query_params.get("title")
        if title:
            self.queryset = self.queryset.filter(title__icontains=title)

        return self.queryset


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
        date = self.request.query_params.get("date")
        movies_id = self.request.query_params.get("movie")
        self.queryset = self.queryset.select_related("cinema_hall", "movie")

        if date:
            date = date.split("-")
            self.queryset = self.queryset.filter(show_time__year=date[0],
                                                 show_time__month=date[1],
                                                 show_time__day=date[2])

        if movies_id:
            movies_id = [int(num) for num in movies_id.split(",")]
            self.queryset = self.queryset.filter(movie_id__in=movies_id)

        if self.action == "list":
            self.queryset = (
                self.queryset.prefetch_related("tickets").annotate(
                    tickets_available=F("cinema_hall__seats_in_row") * F(
                        "cinema_hall__rows") - Count("tickets")))

        return self.queryset


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 25


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__movie_session__cinema_hall").prefetch_related(
                "tickets__movie_session__movie")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
