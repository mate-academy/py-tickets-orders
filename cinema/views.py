from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from datetime import datetime

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
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

    @staticmethod
    def params_to_list_int(params: str) -> list[int]:
        return [int(num) for num in params.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        actors_params = self.request.query_params.get("actors")
        genres_params = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors_params:
            actors_ids = self.params_to_list_int(actors_params)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres_params:
            genres_ids = self.params_to_list_int(genres_params)
            queryset = queryset.filter(genres__id__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset.distinct()

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
        if self.action == "list":
            self.queryset = self.queryset.select_related("cinema_hall").annotate(
                tickets_available=F("cinema_hall__seats_in_row") * F("cinema_hall__rows") - Count("tickets")
            )
            movie = self.request.query_params.get("movie")
            date_str = self.request.query_params.get("date")
            if movie:
                self.queryset = self.queryset.filter(movie_id=int(movie))
            if date_str:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                self.queryset = self.queryset.filter(
                    show_time__year=date.year,
                    show_time__month=date.month,
                    show_time__day=date.day
                )

        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return self.serializer_class


class OrderSetPagination(PageNumberPagination):
    page_size = 2


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    pagination_class = OrderSetPagination
        
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)