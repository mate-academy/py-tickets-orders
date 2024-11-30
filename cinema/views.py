from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    OrderListSerializer,
    OrderSerializer,
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
        """Converts a string of format '1,2,3' to a list of integers [1,2,3]"""
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        name_param = ", ".join(self.request.query_params.keys())
        facilities = self.request.query_params.get(name_param, None)

        if name_param == "actors":
            facilities_ids = self._params_to_ints(facilities)
            queryset = Movie.objects.filter(
                actors__id__in=facilities_ids
            ).distinct()
        if name_param == "genres":
            facilities_ids = self._params_to_ints(facilities)
            queryset = Movie.objects.filter(
                genres__id__in=facilities_ids
            ).distinct()
        if name_param == "title":
            queryset = Movie.objects.filter(
                title__icontains=facilities
            ).distinct()

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
        date_param = self.request.query_params.get("date")
        movie_param = self.request.query_params.get("movie")

        if date_param and not movie_param:
            queryset = MovieSession.objects.filter(
                show_time__date=date_param
            ).distinct()
        if not date_param and movie_param:
            queryset = MovieSession.objects.filter(
                movie__id__exact=movie_param
            ).distinct()
        if date_param and movie_param:
            queryset = MovieSession.objects.filter(
                show_time__date=date_param,
                movie__id__exact=movie_param
            ).distinct()
        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall", "movie")
                .annotate(
                    tickets_available=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )
        elif self.action == "retrieve":
            queryset = queryset.select_related("cinema_hall", "movie")
        return queryset.order_by("id")


class OrderResultsSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderResultsSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall"
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderListSerializer
        return serializer
