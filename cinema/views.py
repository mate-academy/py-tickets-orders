from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    Prefetch,
)
from django.utils.dateparse import parse_date
from rest_framework import permissions, viewsets

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket,
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
    OrderCreateSerializer,
    OrderListSerializer,
)


def _params_to_ints(query_params, param_name):
    values = query_params.get(param_name)

    if not values:
        return None

    try:
        return [int(value) for value in values.split(",") if value.strip()]
    except ValueError:
        return []


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
        queryset = self.queryset.prefetch_related("genres", "actors")
        genres = _params_to_ints(self.request.query_params, "genres")
        actors = _params_to_ints(self.request.query_params, "actors")
        title = self.request.query_params.get("title")

        if genres is not None:
            queryset = queryset.filter(genres__id__in=genres)

        if actors is not None:
            queryset = queryset.filter(actors__id__in=actors)

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
        queryset = self.queryset.select_related(
            "movie", "cinema_hall"
        ).prefetch_related(
            "movie__genres",
            "movie__actors",
            "tickets",
        )
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            if parse_date(date) is None:
                return queryset.none()

            queryset = queryset.filter(show_time__date=date)

        if movie:
            try:
                movie = int(movie)
            except ValueError:
                return queryset.none()

            queryset = queryset.filter(movie_id=movie)

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets"),
                    output_field=IntegerField(),
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        tickets_queryset = Ticket.objects.select_related(
            "movie_session__movie",
            "movie_session__cinema_hall",
        )

        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(Prefetch("tickets", queryset=tickets_queryset))
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer

        return OrderListSerializer
