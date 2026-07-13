from django.db.models import Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated

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
    OrderCreateSerializer,
    OrderSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by("id")
    serializer_class = GenreSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
    serializer_class = ActorSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all().order_by("id")
    serializer_class = CinemaHallSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related(
        "genres",
        "actors",
    ).order_by("id")
    serializer_class = MovieSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset

        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(
                title__icontains=title
            )

        if genres:
            queryset = queryset.filter(
                genres__id__in=genres.split(",")
            )

        if actors:
            queryset = queryset.filter(
                actors__id__in=actors.split(",")
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie",
        "cinema_hall",
    ).annotate(
        tickets_count=Count("tickets")
    ).order_by("id")
    serializer_class = MovieSessionSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time=date)

        if movie:
            queryset = queryset.filter(
                movie_id=movie
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall",
    ).order_by("id")
    # Ativa explicitamente a paginação apenas para os Pedidos
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer

        return OrderSerializer
