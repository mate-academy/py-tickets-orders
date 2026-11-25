from rest_framework import viewsets
from django.db.models import F, Count
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
    OrderListSerializer,
    OrderSerializer,
    TicketMovieSessionListSerializer
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

    @staticmethod
    def query_params_to_list(query_str: str) -> list:
        return [int(id_str) for id_str in query_str.split(",")]

    def get_queryset(self):
        if self.action == "list":
            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            title = self.request.query_params.get("title")
            if actors:
                actors_ids = self.query_params_to_list(actors)
                self.queryset = self.queryset.filter(
                    actors__id__in=actors_ids
                )
            if genres:
                genres_ids = self.query_params_to_list(genres)
                self.queryset = self.queryset.filter(
                    genres__id__in=genres_ids
                )
            if title:
                self.queryset = self.queryset.filter(
                    title__icontains=title
                )
        return self.queryset.prefetch_related(
            "genres", "actors"
        ).distinct()


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
        if self.action == "list":
            date_filter = self.request.query_params.get("date")
            movie_filter = self.request.query_params.get("movie")
            if date_filter:
                self.queryset = self.queryset.filter(
                    show_time__date=date_filter
                )
            if movie_filter:
                self.queryset = self.queryset.filter(
                    movie=movie_filter
                )
        self.queryset = self.queryset.annotate(
            tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                - Count("tickets")
            )
        )
        self.queryset = self.queryset.select_related(
            "movie", "cinema_hall"
        )
        return self.queryset


class OrderPagination(PageNumberPagination):
    page_size = 3
    max_page_size = 12
    page_query_param = "page_size"

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "create":
            return OrderSerializer
        return OrderListSerializer

    def get_queryset(self):
        if self.action == "list":
            self.queryset = self.queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
        authenticated_user = (
            self.request.user if self.request.user.is_authenticated else None
        )
        if authenticated_user:
            self.queryset = self.queryset.filter(user=authenticated_user)
            return self.queryset
        return self.queryset.none()

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)
