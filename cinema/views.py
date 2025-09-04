from datetime import datetime

from django.db.models import QuerySet, F, Count
from rest_framework import viewsets, serializers

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Ticket, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, TicketSerializer, TicketCreateSerializer, OrderSerializer, OrderCreateSerializer,
)

from rest_framework.pagination import PageNumberPagination

class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 100




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
        qs = Movie.objects.all()
        title_param = self.request.query_params.get("title")
        genres_param = self.request.query_params.get("genres")
        actors_param = self.request.query_params.get("actors")

        if title_param:
            qs = qs.filter(title__icontains=title_param)

        if genres_param:
            try:
                genres = [int(g) for g in genres_param.split(",")]
                qs = qs.filter(genres__id__in=genres).distinct()
            except ValueError:
                qs = qs.none()

        if actors_param:
            try:
                actors = [int(a) for a in actors_param.split(",")]
                qs = qs.filter(actors__id__in=actors).distinct()
            except ValueError:
                qs = qs.none()

        return qs.prefetch_related("genres", "actors")


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if movie:
            queryset = queryset.filter(movie_id=int(movie))

        if self.action == "list":
            queryset = (
                queryset.
                select_related("movie", "cinema_hall").
                annotate(
                    tickets_available=F("cinema_hall__rows"
                                        ) * F("cinema_hall__seats_in_row"
                                              ) - Count("tickets")
                )
            )
        elif self.action == "retrieve":
            queryset = queryset.select_related("movie", "cinema_hall").prefetch_related("tickets")

        return queryset.distinct()

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_queryset(self) -> QuerySet[Ticket]:
        queryset = self.queryset
        if self.action in ['list', 'retrieve']:
            return Ticket.objects.prefetch_related("movie_session")
        return queryset

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == 'list':
            return TicketSerializer
        elif self.action in ['update', 'create', 'partial_update']:
            return TicketCreateSerializer
        return  TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderSerializer
        return OrderCreateSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)