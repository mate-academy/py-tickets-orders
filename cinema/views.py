from datetime import date

from django.db.models import Prefetch, QuerySet
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination

from .models import Actor, CinemaHall, Genre, Movie, MovieSession, Order
from .serializers import (
    ActorDetailSerializer,
    ActorListSerializer,
    CinemaHallDetailSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieCreateUpdateSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    MovieSessionCreateUpdateSerializer,
    MovieSessionDetailSerializer,
    MovieSessionListSerializer,
    OrderCreateSerializer,
    OrderSerializer,
)


class DefaultPageNumberPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


# =========================
# ACTOR
# =========================
class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("retrieve", "create", "update", "partial_update"):
            return ActorDetailSerializer
        return ActorListSerializer


# =========================
# GENRE
# =========================
class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by("id")
    serializer_class = GenreSerializer
    pagination_class = None


# =========================
# CINEMA HALL
# =========================
class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all().order_by("id")
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CinemaHallDetailSerializer
        return CinemaHallSerializer


# =========================
# MOVIE
# =========================
class MovieViewSet(viewsets.ModelViewSet):
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MovieCreateUpdateSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieListSerializer

    def get_queryset(self) -> QuerySet:
        queryset = (
            Movie.objects.all()
            .order_by("id")
            .prefetch_related(
                Prefetch(
                    "genres",
                    queryset=Genre.objects.all().order_by("id"),
                ),
                Prefetch(
                    "actors",
                    queryset=Actor.objects.all().order_by("id"),
                ),
            )
        )

        params = getattr(self.request, "query_params", {})
        actor_id = params.get("actors")
        genre_id = params.get("genres")
        title = params.get("title")

        if actor_id:
            try:
                queryset = queryset.filter(actors__id=int(actor_id))
            except (TypeError, ValueError):
                pass

        if genre_id:
            try:
                queryset = queryset.filter(genres__id=int(genre_id))
            except (TypeError, ValueError):
                pass

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


# =========================
# MOVIE SESSION
# =========================
class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        MovieSession.objects.select_related("movie", "cinema_hall")
        .all()
        .order_by("id")
    )
    # testes esperam lista (sem paginação nesta rota)
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MovieSessionCreateUpdateSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionListSerializer

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        params = getattr(self.request, "query_params", {})

        movie_param = params.get("movie")
        if movie_param:
            try:
                queryset = queryset.filter(movie_id=int(movie_param))
            except (TypeError, ValueError):
                return queryset.none()

        date_str = params.get("date")
        if date_str:
            parsed_date = None
            try:
                parsed_date = date.fromisoformat(date_str)
            except ValueError:
                try:
                    y, m, d = (int(x) for x in date_str.split("-"))
                    parsed_date = date(y, m, d)
                except Exception:
                    parsed_date = None

            if parsed_date is not None:
                queryset = queryset.filter(show_time__date=parsed_date)

        return queryset


# =========================
# ORDER
# =========================
class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self) -> QuerySet:
        return (
            Order.objects.filter(user=self.request.user)
            .order_by("id")
            .select_related("user")
            .prefetch_related(
                "tickets",
                "tickets__movie_session",
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer
