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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = [int(actor_id) for actor_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)
        elif genres:
            genres_ids = [int(genre_id) for genre_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)
        elif title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 10


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = MovieSessionListSerializer
            return serializer

        if self.action == "retrieve":
            serializer = MovieSessionDetailSerializer
            return serializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.select_related().annotate(
                tickets_available=F("cinema_hall__seats_in_row")
                * F("cinema_hall__rows")
                - Count("tickets")
            )

            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")

            if date:
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.filter(movie__id=movie)

        return queryset


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie"
            ).prefetch_related("tickets__movie_session__cinema_hall")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            return OrderListSerializer

        return serializer
