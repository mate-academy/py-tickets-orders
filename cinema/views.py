from django.utils.dateparse import parse_date
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
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, TicketSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 3


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by("id")
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all().order_by("id")
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
        queryset = Movie.objects.all().order_by("id")

        genres_param = self.request.query_params.get("genres")
        if genres_param:
            try:
                genres = [int(g) for g in genres_param.split(",")
                          if g.isdigit()]
                if genres:
                    queryset = queryset.filter(genres__id__in=genres)
            except ValueError:
                pass

        actors_param = self.request.query_params.get("actors")
        if actors_param:
            try:
                actors = [int(a) for a in actors_param.split(",")
                          if a.isdigit()]
                if actors:
                    queryset = queryset.filter(actors__id__in=actors)
            except ValueError:
                pass

        title = self.request.query_params.get("title")
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
        queryset = MovieSession.objects.all().order_by("id")
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                queryset = queryset.filter(
                    show_time__date=parsed_date
                )
        if movie:
            queryset = queryset.filter(movie__id=movie)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
