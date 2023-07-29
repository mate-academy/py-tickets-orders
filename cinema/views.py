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
    TicketListSerializer,
    TicketSerializer,
    OrderListSerializer,
    TakenTicketSerializer,
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
    queryset = Movie.objects.prefetch_related(
        "genres", "actors"
    )
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
            actors_ids = [
                int(actor_id)
                for actor_id in actors.split(",")
            ]
            queryset = Movie.objects.filter(actors__in=actors_ids)

        if genres:
            genres_ids = [
                int(genres_id)
                for genres_id in genres.split(",")
            ]
            queryset = Movie.objects.filter(genres__in=genres_ids)

        if title:
            queryset = Movie.objects.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie", "cinema_hall"
    )
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        show_time = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                )
            )

            if show_time:
                queryset = queryset.filter(show_time__date=show_time)

            if movie:
                queryset = queryset.filter(movie__id=int(movie))

        return queryset


class TakenTicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.filter(order__isnull=False)
    serializer_class = TakenTicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related(
        "order", "movie_session"
    )
    serializer_class = TicketSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer

        return TicketSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets")
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer
