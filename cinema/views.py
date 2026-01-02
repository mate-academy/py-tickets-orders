from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models.aggregates import Count
from rest_framework import viewsets

from cinema.models import (Genre,
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
    OrderListSerializer,
    OrderCreateSerializer
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
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actor_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)

        if genres:
            genre_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def _params_to_ints(self, qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    pagination_class = None

    def get_queryset(self):
        queryset = (
            self.queryset
            .select_related("movie", "cinema_hall")
            .annotate(
                tickets_available=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets"),
                    output_field=IntegerField()
                )
            )
        )

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer
