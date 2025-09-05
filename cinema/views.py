from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from cinema.serializers import OrderSerializer, OrderCreateSerializer
from django_filters.rest_framework import DjangoFilterBackend
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from rest_framework import filters


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
        queryset = Movie.objects.all()
        actors = self.request.GET.get("actors")
        genres = self.request.GET.get("genres")
        title = self.request.GET.get("title")
        if actors:
            actor_ids = [
                int(a) for a in actors.split(",") if a.isdigit()
            ]
            queryset = queryset.filter(actors__id__in=actor_ids)
        if genres:
            genre_ids = [
                int(g) for g in genres.split(",") if g.isdigit()
            ]
            queryset = queryset.filter(genres__id__in=genre_ids)
        if title:
            queryset = queryset.filter(title__icontains=title)
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

        queryset = MovieSession.objects.select_related(
            "movie", "cinema_hall"
        ).prefetch_related("tickets")
        movie = self.request.GET.get("movie")
        date = self.request.GET.get("date")
        if movie:
            queryset = queryset.filter(movie__id=movie)
        if date:
            queryset = queryset.filter(show_time__date=date)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects \
            .filter(user=self.request.user) \
            .order_by("-created_at")
