from django.db.models import F, Count
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Movie, MovieSession, Order
from .serializers import (
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionDetailSerializer,
    OrderSerializer,
)

class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100

class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Filter orders by the authenticated user
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MovieViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        
        # Filtering by title (contains)
        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        # Filtering by genres (comma-separated IDs)
        genres = self.request.query_params.get("genres")
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)

        # Filtering by actors (comma-separated IDs)
        actors = self.request.query_params.get("actors")
        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        # Date filtering (YYYY-MM-DD)
        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)

        # Movie ID filtering
        movie_id = self.request.query_params.get("movie")
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        # Annotate tickets_available
        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=F("cinema_hall__capacity") - Count("tickets")
            )

        return queryset.select_related("movie", "cinema_hall")
