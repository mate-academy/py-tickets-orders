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
    OrderCreateSerializer,
    OrderSerializer,
    OrderListSerializer,
    TicketSerializer,
)


def params_to_ints(string_ids):
    return [int(str_id) for str_id in string_ids.split(",")]


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
        queryset = Movie.objects.prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_id = params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_id)
        if genres:
            genres_id = params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_id)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


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
        queryset = MovieSession.objects.all()
        query_params = self.request.query_params

        movie = query_params.get("movie")
        date = query_params.get("date")
        start_time = query_params.get("start_time")
        min_tickets_available = query_params.get("min_tickets_available")

        if movie:
            movie_ids = params_to_ints(movie)
            queryset = queryset.filter(movie__id__in=movie_ids)

        if date:
            queryset = queryset.filter(show_time__date=date)

        if start_time:
            queryset = queryset.filter(show_time__time__gte=start_time)

        if self.action == "list":
            queryset = queryset.select_related("cinema_hall", "movie")
            for session in queryset:
                session.tickets_available = (
                    session.cinema_hall.rows
                    * session.cinema_hall.seats_in_row
                    - session.tickets.count()
                )

        if min_tickets_available:
            queryset = [
                session for session in queryset
                if session.tickets_available >= int(min_tickets_available)
            ]

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 1
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
