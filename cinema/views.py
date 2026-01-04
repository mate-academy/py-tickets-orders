from rest_framework import (
    filters,
    viewsets,
)
from rest_framework.permissions import IsAuthenticated

from django_filters import rest_framework as django_filters
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
)

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    MovieSessionSerializer,
    OrderListSerializer,
    OrderSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by("name")
    serializer_class = GenreSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("last_name", "first_name")
    serializer_class = ActorSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name"]


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all().order_by("name")
    serializer_class = CinemaHallSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class MovieFilter(FilterSet):
    genres = django_filters.NumberFilter(field_name="genres__id",
                                         lookup_expr="exact")
    actors = django_filters.NumberFilter(field_name="actors__id",
                                         lookup_expr="exact")
    title = django_filters.CharFilter(field_name="title",
                                      lookup_expr="icontains")

    class Meta:
        model = Movie
        fields = ["genres", "actors", "title"]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all().order_by("title")
    serializer_class = MovieSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = MovieFilter
    search_fields = ["title"]

    def get_queryset(self):
        return super().get_queryset().distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionFilter(FilterSet):
    movie = django_filters.NumberFilter(field_name="movie",
                                        lookup_expr="exact")
    date = django_filters.DateFilter(field_name="show_time",
                                     lookup_expr="date")

    class Meta:
        model = MovieSession
        fields = ["movie", "date"]


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all().order_by("-show_time")
    serializer_class = MovieSessionSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = MovieSessionFilter

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
