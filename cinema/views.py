import datetime
from rest_framework import viewsets
from django.db.models import F, Count, ExpressionWrapper, IntegerField

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.pagination import NoWrapPagination
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
    OrderSerializer,
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        genres = self.request.query_params.get("genres")  # type: ignore
        if genres:
            genre_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genre_ids).distinct()

        actors = self.request.query_params.get("actors")  # type: ignore
        if actors:
            actor_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actor_ids).distinct()

        title = self.request.query_params.get("title")  # type: ignore
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset.select_related("movie", "cinema_hall")
                .annotate(
                    capacity=ExpressionWrapper(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row"),  # noqa: E501
                        output_field=IntegerField(),
                    ),
                    tickets_count=Count("tickets"),
                )
                .annotate(
                    tickets_available=ExpressionWrapper(
                        F("capacity") - F("tickets_count"),
                        output_field=IntegerField(),
                    )
                )
                .order_by("id")
            )

            movie = self.request.query_params.get("movie")  # type: ignore
            if movie:
                queryset = queryset.filter(movie__id=int(movie))

            date_str = self.request.query_params.get("date")  # type: ignore
            if date_str:
                try:
                    date_obj = (
                        datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    )
                    queryset = queryset.filter(show_time__date=date_obj)
                except ValueError:
                    pass

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = NoWrapPagination

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
