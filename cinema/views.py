from datetime import datetime

from django.db.models import Q, F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    MovieListSerializer, OrderSerializer, OrderListSerializer,
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
    def _params_to_ints(query_string):
        """
        Converts a string of format '1,2,3' to a list of integers [1, 2, 3].
        """
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        title_str = self.request.query_params.get("title")
        actor_ids = self.request.query_params.get("actors")
        genre_ids = self.request.query_params.get("genres")

        filters = Q()

        if title_str:
            filters |= Q(title__icontains=title_str)

        if actor_ids:
            actor_ids = self._params_to_ints(actor_ids)
            filters |= Q(actors__id__in=actor_ids)

        if genre_ids:
            genre_ids = self._params_to_ints(genre_ids)
            filters |= Q(genres__id__in=genre_ids)

        if filters:
            queryset = queryset.filter(filters).distinct()

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset


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
        queryset = self.queryset

        movie_id = self.request.query_params.get("movie")
        date_str = self.request.query_params.get("date")

        filters = Q()

        if movie_id:
            filters &= Q(movie=movie_id)

        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                filters &= Q(show_time__date=date)
            except ValueError:
                pass

        if filters:
            queryset = queryset.filter(filters).distinct()

        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=F(
                        "cinema_hall__seats_in_row"
                    ) * F("cinema_hall__rows") - Count("tickets")
                )
            )
        elif self.action == "retrieve":
            queryset = queryset.select_related("movie", "cinema_hall")

        return queryset


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
