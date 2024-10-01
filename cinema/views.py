from django.db.models import QuerySet, Count, F
from rest_framework import viewsets

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
)
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
    OrderListSerializer,
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

    @staticmethod
    def _params_to_int(query_string: str) -> list[int]:
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.prefetch_related("genres", "actors")

            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            string = self.request.query_params.get("title")
            if actors:
                actors = self._params_to_int(actors)
                queryset = queryset.filter(actors__id__in=actors)
            if genres:
                genres = self._params_to_int(genres)
                queryset = queryset.filter(genres__id__in=genres)
            if string:
                queryset = queryset.filter(title__icontains=string)

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset.distinct()

    def get_serializer_class(self) -> type[MovieSerializer]:
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset
                .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows")
                        * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

            movie = self.request.query_params.get("movie")
            date = self.request.query_params.get("date")
            if movie:
                queryset = queryset.filter(movie_id=int(movie))
            if date:
                queryset = queryset.filter(show_time__date=date)

        if self.action == "retrieve":
            queryset = queryset.select_related("movie", "cinema_hall")
        return queryset

    def get_serializer_class(self) -> type[MovieSessionSerializer]:
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_serializer_class(self) -> type[OrderSerializer]:
        serializer = self.serializer_class
        if self.action == "list":
            serializer = OrderListSerializer
        return serializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )

        return queryset

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
