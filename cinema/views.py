import datetime

# from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, F
from rest_framework import viewsets, filters

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession, Order
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
    OrderSerializer, OrderPagination
)


def params_to_ints(qs: str):
    return [int(str_id) for str_id in qs.split(",")]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieCustomFilter(filters.SearchFilter):
    """
    Here I added custom class for search by title
    """
    search_param = "title"


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    """
    I can filter with just 3 lines of code, but because 
    of the tests I was forced to write more longer code :)
    
    Realisation below ↓
    
    filter_backends = [MovieCustomFilter, DjangoFilterBackend]
    search_fields = ["title"]
    filterset_fields = ["actors", "genres"]
    """

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = params_to_ints(actors)
            self.queryset = self.queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = params_to_ints(genres)
            self.queryset = self.queryset.filter(genres__id__in=genres_ids)

        if title:
            self.queryset = self.queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            self.queryset = self.queryset.prefetch_related(
                "genres", "actors"
            )

        return self.queryset.distinct()

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
        date_info = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date_info:
            date = datetime.datetime.strptime(date_info, "%Y-%m-%d")
            self.queryset = self.queryset.filter(show_time__year=date.year,
                                                 show_time__month=date.month,
                                                 show_time__day=date.day)

        if movie:
            movie_ids = params_to_ints(movie)
            self.queryset = self.queryset.filter(movie_id__in=movie_ids)

        if self.action == "list":
            return self.queryset.select_related(
                "movie", "cinema_hall").annotate(
                tickets_available=F(
                    "cinema_hall__rows") * F(
                    "cinema_hall__seats_in_row") - Count(
                    "tickets")
            )

        return self.queryset.distinct()


class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__cinema_hall"
        )

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)
