from datetime import datetime

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated

from .models import Movie, MovieSession, Order
from .serializers import (
    MovieSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


# ────────────────────────────────
# MOVIE LIST VIEW + FILTERS
# ────────────────────────────────
class MovieListView(generics.ListAPIView):
    serializer_class = MovieSerializer

    def get_queryset(self):
        qs = Movie.objects.all()

        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            qs = qs.filter(title__icontains=title)

        if genres:
            qs = qs.filter(genres__name__icontains=genres)

        if actors:
            qs = qs.filter(actors__full_name__icontains=actors)

        return qs


# ────────────────────────────────
# MOVIE SESSION LIST VIEW + FILTERS
# ────────────────────────────────
class MovieSessionListView(generics.ListAPIView):
    serializer_class = MovieSessionListSerializer

    def get_queryset(self):
        qs = MovieSession.objects.select_related("movie", "cinema_hall")

        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            qs = qs.filter(show_time__date=parsed_date)

        if movie_id:
            qs = qs.filter(movie__id=movie_id)

        return qs


# ────────────────────────────────
# MOVIE SESSION DETAIL VIEW
# ────────────────────────────────
class MovieSessionDetailView(generics.RetrieveAPIView):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionDetailSerializer


# ────────────────────────────────
# ORDERS
# ────────────────────────────────
class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("tickets")
