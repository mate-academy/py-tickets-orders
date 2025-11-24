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
    Ticket,
)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionRetrieveSerializer,
    MovieListSerializer,
    OrderSerializer,
    TicketSerializer,
    OrderListSerializer,
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors:
            actors_ids = list(map(int, actors.split(",")))
            self.queryset = self.queryset.filter(actors__id__in=actors_ids)
        if genres:
            genres_ids = list(map(int, genres.split(",")))
            self.queryset = self.queryset.filter(genres__id__in=genres_ids)
        if title:
            self.queryset = self.queryset.filter(title__icontains=title)
        return self.queryset.distinct()

    def get_serializer_class(self):

        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall",)
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie:
            movie_ids = list(map(int, movie.split(",")))
            self.queryset = self.queryset.filter(movie_id__in=movie_ids)
        if date:
            self.queryset = self.queryset.filter(show_time__date=date)
        if self.action == "list":
            self.queryset = self.queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )
        return self.queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionRetrieveSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = (
        Ticket.objects
        .select_related(
            "movie_session__movie",
            "movie_session__cinema_hall",
            "order",
        )
        .prefetch_related(
            "movie_session__movie__genres",
            "movie_session__movie__actors",
        )
    )
    serializer_class = TicketSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 1000


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets",
        "tickets__movie_session",
        "tickets__movie_session__cinema_hall",
        "tickets__movie_session__movie__genres",
        "tickets__movie_session__movie__actors",
    ).select_related()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer
        return OrderSerializer
