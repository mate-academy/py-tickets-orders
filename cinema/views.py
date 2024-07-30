from django.db.models import F, Count
from django_filters import FilterSet, DateFilter, BaseInFilter
from django_filters.rest_framework import DjangoFilterBackend, filters
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
    MovieListSerializer, OrderSerializer,
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


class MovieFilter(FilterSet):
    genres = BaseInFilter(field_name="genres__id", lookup_expr="in")
    actors = BaseInFilter(field_name="actors__id", lookup_expr="in")
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = Movie
        fields = ["actors", "genres", "title"]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MovieFilter

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionFilter(FilterSet):
    date = DateFilter(field_name="show_time", lookup_expr="date")
    movie = filters.CharFilter(field_name="movie__id", lookup_expr="exact")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MovieSessionFilter

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        if self.action == "list":
            queryset = self.queryset
            if self.action == "list":
                queryset = (
                    queryset
                    .annotate(
                        tickets_available=(
                            F("cinema_hall__rows")
                            * F("cinema_hall__seats_in_row")
                            - Count("tickets"))
                    )
                ).order_by("id")
            return queryset


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
