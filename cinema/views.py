from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, CreateOrderSerializer, OrderSerializer,
)


class BaseViewSet(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        response.data = response.data["results"]
        return response


class GenreViewSet(BaseViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(BaseViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(BaseViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(BaseViewSet):
    queryset = Movie.objects.all().select_related()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        if self.action == "list" and title:
            queryset = queryset.filter(title__icontains=title)
        if self.action == "list" and actors:
            queryset = queryset.prefetch_related("actors").filter(
                actors__id=actors)
        if self.action == "list" and genres:
            genres = self._params_to_ints(genres)
            queryset = queryset.prefetch_related("genres").filter(
                genres__id__in=genres)
        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        response.data = response.data["results"]
        return response

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            genres = self.request.query_params.get("genres")

            queryset = queryset.select_related("cinema_hall").annotate(
                tickets_available=F("cinema_hall__rows") * F(
                    "cinema_hall__seats_in_row") - Count("tickets"))

            if date:
                queryset = queryset.filter(show_time__date=date)
            if movie:
                queryset = queryset.select_related("movie").filter(
                    movie__id=movie)
            if genres:
                genres = self._params_to_ints(genres)
                queryset = queryset.prefetch_related("genres").filter(
                    genres__id__in=genres)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects.select_related().filter(user=self.request.user)
