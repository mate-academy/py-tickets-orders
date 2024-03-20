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
        actors = self.request.query_params.getlist("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            actor_ids = [int(id_) for id_ in actors]
            queryset = queryset.filter(actors__in=actor_ids)
        if genres:
            genre_ids = [int(id_) for id_ in genres.split(",")]
            queryset = queryset.filter(genres__in=genre_ids)

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

        movie_ids = self.request.query_params.get("movie")
        show_time = self.request.query_params.get("date")

        if movie_ids:

            queryset = queryset.filter(
                movie_id__in=[int(n) for n in movie_ids.split(",")]
            )
        if show_time:
            year = show_time.split("-")[0]
            month = show_time.split("-")[1]
            day = show_time.split("-")[2]

            queryset = queryset.filter(
                show_time__year=year,
                show_time__day=day,
                show_time__month=month
            )

        if self.action == "list":
            queryset = (
                queryset
                .select_related()
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 5


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__cinema_hall",
        "tickets__movie_session__movie"
    )
    serializer_class = OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderListSerializer

        return serializer
