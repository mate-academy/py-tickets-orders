from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from cinema.models import (Genre,
                           Actor, CinemaHall, Movie,
                           MovieSession, Order)

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
    OrderListSerializer, OrderCreateSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Movie.objects.all()
        genres = self.request.GET.get("genres")
        actors = self.request.GET.get("actors")
        title = self.request.GET.get("title")

        if genres:
            queryset = queryset.filter(genres__id__in=genres.split(","))

        if actors:
            queryset = queryset.filter(actors__id__in=actors.split(","))

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
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        movie_id = self.request.GET.get("movie")
        date = self.request.query_params.get("date")

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer
        return OrderCreateSerializer

    def perform_create(self, serializer):
        serializer.save()
