from django.db.models import Count, F
from rest_framework import viewsets

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order
)

from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
    StandardResultsSetPagination,
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    @staticmethod
    def _params_to_ints(qs: str):
        return [
            int(str_id)
            for str_id in qs.split(",")
        ]

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_id = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_id)
        if genres:
            genres_id = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_id)
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
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie:
            queryset = queryset.filter(movie_id=movie)
        if date:
            queryset = queryset.filter(show_time__date=date)

        if self.action == "list":
            capacity = F("cinema_hall__seats_in_row") * F("cinema_hall__rows")
            queryset = queryset.annotate(
                tickets_available=capacity - Count("tickets")
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user).prefetch_related("tickets")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        if self.action == "create":
            return OrderCreateSerializer

        return OrderListSerializer
