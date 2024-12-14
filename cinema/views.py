from django.db.models import Count, F

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
    OrderGetSerializer,
    OrderCreateSerializer,
)


class MixinParamsToListInt:
    @staticmethod
    def params_to_list_int(query_string):
        return [int(litera) for litera in query_string.split(",")]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(MixinParamsToListInt, viewsets.ModelViewSet):
    queryset = Movie.objects.all().prefetch_related("actors", "genres")
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors = self.params_to_list_int(actors)
            queryset = queryset.filter(
                actors__in=actors)
        if genres:
            genres = self.params_to_list_int(genres)
            queryset = queryset.filter(genres__in=genres)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(MixinParamsToListInt, viewsets.ModelViewSet):
    queryset = MovieSession.objects.all().select_related(
        "movie",
        "cinema_hall"
    ).prefetch_related("tickets").annotate(
        tickets_available=F("cinema_hall__rows") * F(
            "cinema_hall__seats_in_row") - Count("tickets")
    )

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if actors:
            actors = self.params_to_list_int(actors)
            queryset = queryset.filter(movie__actors__in=actors)
        if genres:
            genres = self.params_to_list_int(genres)
            queryset = queryset.filter(movie__genres__in=genres)
        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            movie = self.params_to_list_int(movie)
            queryset = queryset.filter(movie__in=movie)

        return queryset.distinct()


class OrderResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("user").prefetch_related(
        "tickets__movie_session__cinema_hall",
        "tickets__movie_session__movie"
    )

    pagination_class = OrderResultsSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderGetSerializer
        elif self.action == "create":
            return OrderCreateSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
