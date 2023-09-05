from datetime import datetime

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket

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
    OrderSerializer, OrderListSerializer,
    # TicketSerializer,
    # OrderListSerializer,
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
        if self.action == "retrieve":
            return MovieDetailSerializer

        if self.action == "list":
            return MovieListSerializer
        return MovieSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        genres = self.request.query_params.getlist("genres")
        actors = self.request.query_params.getlist("actors")
        title = self.request.query_params.get("title")

        # Filter by genres and actors
        if genres:
            queryset = queryset.filter(genres__name__in=genres)
        if actors:
            queryset = queryset.filter(actors__full_name__in=actors)

        # Filter by title containing the provided string
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionListSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        # Filter by date and movie ID
        if date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d")
                queryset = queryset.filter(show_time__date=date)
            except ValueError:
                # Handle invalid date format gracefully
                queryset = queryset.none()

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
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
