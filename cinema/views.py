from typing import Type
from datetime import date
from django.utils.dateparse import parse_date
from django.db.models import Prefetch, QuerySet, Count
from rest_framework.serializers import Serializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderListSerializer,
    OrderWriteSerializer,
)


class GenreViewSet(ModelViewSet):
    serializer_class = GenreSerializer
    queryset = Genre.objects.all()
    pagination_class = None

    def get_queryset(self) -> QuerySet[Genre]:
        qs = self.queryset
        if self.action == "list":
            return qs.only("id", "name")
        return qs


class ActorViewSet(ModelViewSet):
    serializer_class = ActorSerializer
    queryset = Actor.objects.all()
    pagination_class = None

    def get_queryset(self) -> QuerySet[Actor]:
        qs = self.queryset
        if self.action == "list":
            return qs.only("id", "first_name", "last_name")
        return qs


class CinemaHallViewSet(ModelViewSet):
    serializer_class = CinemaHallSerializer
    queryset = CinemaHall.objects.all()
    pagination_class = None

    def get_queryset(self) -> QuerySet[CinemaHall]:
        qs = self.queryset
        if self.action == "list":
            return qs.only("id", "name", "rows", "seats_in_row")
        return qs


class MovieViewSet(ModelViewSet):
    serializer_class = MovieSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[Movie]:
        movies_query = Movie.objects
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        if title:
            movies_query = movies_query.filter(title__icontains=title)
        if genres:
            g_ids = [int(x) for x in genres.split(",") if x.strip().isdigit()]
            if g_ids:
                movies_query = movies_query.filter(genres__id__in=g_ids)
        if actors:
            a_ids = [int(x) for x in actors.split(",") if x.strip().isdigit()]
            if a_ids:
                movies_query = movies_query.filter(actors__id__in=a_ids)
        if self.action == "list":
            movies_query = movies_query.only(
                "id", "title", "description", "duration"
            ).prefetch_related(
                Prefetch("genres", queryset=Genre.objects.only("id", "name")),
                Prefetch(
                    "actors",
                    queryset=Actor.objects.only(
                        "id", "first_name", "last_name"
                    )
                ),
            )
        else:
            movies_query = movies_query.prefetch_related(
                Prefetch("genres", queryset=Genre.objects.only("id", "name")),
                Prefetch(
                    "actors",
                    queryset=Actor.objects.only(
                        "id", "first_name", "last_name"
                    )
                ),
            )
        return movies_query.distinct()

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionViewSet(ModelViewSet):
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[MovieSession]:
        qs = MovieSession.objects

        movie_param = self.request.query_params.get("movie")
        date_str = self.request.query_params.get("date")

        if movie_param:
            try:
                qs = qs.filter(movie_id=int(str(movie_param).strip()))
            except (TypeError, ValueError):
                pass

        if date_str:
            dates = parse_date(str(date_str).strip())
            if dates:
                qs = qs.filter(show_time__date=dates)

        if self.action == "list":
            return qs.select_related("movie", "cinema_hall").annotate(
                tickets_count=Count("tickets")
            ).only(
                "id",
                "show_time",
                "movie__id",
                "movie__title",
                "cinema_hall__id",
                "cinema_hall__name",
                "cinema_hall__rows",
                "cinema_hall__seats_in_row",
            )

        return qs.select_related(
            "movie", "cinema_hall"
        ).prefetch_related("tickets")

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self) -> QuerySet[Order]:
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        ).order_by("id")

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return OrderListSerializer
        return OrderWriteSerializer
