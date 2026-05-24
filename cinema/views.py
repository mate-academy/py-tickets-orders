from __future__ import annotations

from datetime import datetime

from django.db.models import (
    Count,
    F,
    IntegerField,
    OuterRef,
    QuerySet,
    Subquery,
)
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
    Ticket,
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
    OrderReadSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 10


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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_serializer_class(self) -> type[MovieSerializer]:
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    def get_queryset(self) -> QuerySet:
        queryset = Movie.objects.prefetch_related("genres", "actors")

        actors_param: str | None = (
            self.request.query_params.get("actors")
        )
        genres_param: str | None = (
            self.request.query_params.get("genres")
        )
        title_param: str | None = (
            self.request.query_params.get("title")
        )

        if actors_param:
            actor_ids = [
                int(i) for i in actors_param.split(",")
                if i.isdigit()
            ]
            queryset = queryset.filter(actors__id__in=actor_ids)

        if genres_param:
            genre_ids = [
                int(i) for i in genres_param.split(",")
                if i.isdigit()
            ]
            queryset = queryset.filter(genres__id__in=genre_ids)

        if title_param:
            queryset = queryset.filter(
                title__icontains=title_param
            )

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie", "cinema_hall"
    ).prefetch_related("tickets")
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self) -> type[MovieSessionSerializer]:
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = MovieSession.objects.select_related(
            "movie", "cinema_hall"
        ).prefetch_related("tickets")

        if self.action == "list":
            ticket_count_sq = (
                Ticket.objects.filter(
                    movie_session=OuterRef("pk")
                )
                .values("movie_session")
                .annotate(cnt=Count("id"))
                .values("cnt")
            )
            queryset = queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Subquery(
                        ticket_count_sq,
                        output_field=IntegerField(),
                    )
                )
            )

        date_param: str | None = (
            self.request.query_params.get("date")
        )
        movie_param: str | None = (
            self.request.query_params.get("movie")
        )

        if date_param:
            try:
                parsed_date = datetime.strptime(
                    date_param, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    show_time__date=parsed_date
                )
            except ValueError:
                pass

        if movie_param and movie_param.isdigit():
            queryset = queryset.filter(
                movie__id=int(movie_param)
            )

        return queryset


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    pagination_class = OrderPagination

    def get_queryset(self) -> QuerySet:
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )

    def get_serializer_class(
        self,
    ) -> type[OrderReadSerializer] | type[OrderCreateSerializer]:
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    def perform_create(
        self,
        serializer: OrderCreateSerializer,
    ) -> None:
        serializer.save(user=self.request.user)
