from django.db.models import F, Count
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
    MovieListSerializer,
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

    def get_queryset(self):
        queryset = self.queryset

        queryset = self._filter_by_param(queryset, "actors")
        queryset = self._filter_by_param(queryset, "genres")
        queryset = self._filter_by_title(queryset)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def _filter_by_param(self, queryset, param_name: str):
        param_value = self.request.query_params.get(param_name)

        if param_value:
            param_ids = [int(param_id) for param_id in param_value.split(",")]
            filter_kwargs = {f"{param_name}__id__in": param_ids}
            queryset = queryset.filter(**filter_kwargs)

        return queryset

    def _filter_by_title(self, queryset):
        title = self.request.query_params.get("title")

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        queryset = self._filter_by_movie(queryset)
        queryset = self._filter_by_date(queryset)

        if self.action == "list":
            queryset = (
                queryset.annotate(
                    tickets_available=((F("cinema_hall__seats_in_row")
                                       * F("cinema_hall__rows"))
                                       - Count("tickets"))
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def _filter_by_movie(self, queryset):
        movie = self.request.query_params.get("movie")

        if movie:
            queryset = queryset.filter(movie__id=movie)

        return queryset

    def _filter_by_date(self, queryset):
        date = self.request.query_params.get("date")

        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 55


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
