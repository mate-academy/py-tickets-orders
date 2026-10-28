from django.utils.dateparse import parse_date
from rest_framework import viewsets, mixins, permissions
from rest_framework.pagination import PageNumberPagination
from .models import Movie, MovieSession as MS, Order
from .serializers import (
    MovieListSerializer, MovieSessionListSerializer,
    MovieSessionDetailSerializer, OrderListCreateSerializer,
    OrderCreateSerializer
)


class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class MovieViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Movie.objects.all().prefetch_related("genres",
                                                    "actors")
    serializer_class = MovieListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        title = self.request.query_params.get("title")
        if title:
            qs = qs.filter(title__icontains=title)
        genres = self.request.query_params.get("genres")
        if genres:
            ids = [int(x) for x in genres.split(",") if x.isdigit()]
            if ids:
                qs = qs.filter(genres__id__in=ids).distinct()
        actors = self.request.query_params.get("actors")
        if actors:
            ids = [int(x) for x in actors.split(",") if x.isdigit()]
            if ids:
                qs = qs.filter(actors__id__in=ids).distinct()
        return qs


class MovieSessionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = MS.objects.select_related("movie", "cinema_hall")
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        date_str = self.request.query_params.get("date")
        if date_str:
            d = parse_date(date_str)
            if d:
                qs = qs.filter(show_time__date=d)
        movie = self.request.query_params.get("movie")
        if movie and movie.isdigit():
            qs = qs.filter(movie_id=int(movie))
        return qs.order_by("show_time")


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "tickets",
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListCreateSerializer

    def perform_create(self, serializer):
        serializer.save()
