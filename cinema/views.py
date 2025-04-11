from django.contrib.auth.models import AnonymousUser
from django.utils.dateparse import parse_date

from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (Genre, Actor, CinemaHall,
                           Movie, MovieSession, Order, Ticket)

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
    OrderCreateSerializer,
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
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()

    def get_queryset(self):
        queryset = self.queryset

        genre_params = self.request.query_params.get("genres", None)
        if genre_params:
            genre_params = genre_params.split(",")
            queryset = queryset.filter(genres__in=genre_params)

        actors_params = self.request.query_params.get("actors", None)

        if actors_params:
            actors_params = actors_params.split(",")
            queryset = queryset.filter(actors__in=actors_params)

        title_params = self.request.query_params.get("title", None)
        if title_params:
            title_params = title_params.split(",")
            for title in title_params:
                queryset = queryset.filter(title__icontains=title)

        return queryset.prefetch_related("actors", "genres").distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            movie_params = self.request.query_params.get("movie", None)
            if movie_params:
                movie_params = movie_params.split(",")
                queryset = queryset.filter(movie_id__in=movie_params)

            date_params = self.request.query_params.get("date", None)
            if date_params:
                date_params = date_params.split(",")
                date_params = [parse_date(date) for date in date_params]
                queryset = queryset.filter(show_time__date__in=date_params)

            queryset = (
                queryset.annotate(
                    tickets_available=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets"),
                )
            )
        return (queryset
                .select_related("cinema_hall", "movie")
                )

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketsViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderListPagination(PageNumberPagination):
    page_size = 2
    max_page_size = 2
    page_size_query_param = "page"


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    pagination_class = OrderListPagination

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset

        queryset = queryset.prefetch_related("tickets__movie_session")

        if isinstance(self.request.user, AnonymousUser):
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
