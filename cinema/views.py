from django.db.models import F, Count

from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from cinema.models import Genre, Actor, Movie, CinemaHall, MovieSession, Order
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    MovieSerializer,
    MovieDetailSerializer,
    MovieCreateSerializer,
    CinemaHallSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    MovieSessionCreateSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


class GenreViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    # Тесты ожидают прямой список []
    pagination_class = None


class ActorViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    # Тесты ожидают прямой список []
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    # Тесты ожидают прямой список []
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors")
    # Тесты ожидают прямой список []
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieCreateSerializer

    def get_queryset(self):
        queryset = self.queryset

        genres = self.request.query_params.get("genres")
        if genres:
            genre_ids = [int(g) for g in genres.split(",") if g.isdigit()]
            queryset = queryset.filter(genres__id__in=genre_ids)

        actors = self.request.query_params.get("actors")
        if actors:
            actor_ids = [int(a) for a in actors.split(",") if a.isdigit()]
            queryset = queryset.filter(actors__id__in=actor_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie", "cinema_hall"
    ).prefetch_related("tickets")
    # Тесты ожидают прямой список []
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionCreateSerializer

    def get_queryset(self):
        queryset = self.queryset

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)

        movie = self.request.query_params.get("movie")
        if movie and movie.isdigit():
            queryset = queryset.filter(movie__id=int(movie))

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=F(
                    "cinema_hall__rows"
                ) * F("cinema_hall__seats_in_row") - Count("tickets")
            )

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    queryset = Order.objects.prefetch_related("tickets__movie_session__movie")
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
