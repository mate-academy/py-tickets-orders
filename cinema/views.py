import datetime

from django.db.models import (
    F,
    Count
)
from rest_framework import (
    viewsets,
    mixins
)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

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
    OrderCreateSerializer,
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
        queryset = self.queryset.prefetch_related("genres", "actors")
        query_params = self.request.query_params
        actors = query_params.get("actors")
        genres = query_params.get("genres")
        title = query_params.get("title")
        try:
            if actors:
                actors = [int(actor_id) for actor_id in actors.split(",")]
                queryset = queryset.filter(actors__id__in=actors)
            if genres:
                genres = [int(genre_id) for genre_id in genres.split(",")]
                queryset = queryset.filter(genres__id__in=genres)
        except ValueError:
            raise ValidationError({
                "detail": "Invalid query parameters. IDs must be integers "
                          "separated by commas."
            })
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
        queryset = self.queryset.select_related("movie", "cinema_hall")
        query_params = self.request.query_params
        date = query_params.get("date")
        movie = query_params.get("movie")

        if date:
            try:
                parsed_date = datetime.datetime.strptime(
                    date,
                    "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(show_time__date=parsed_date)
            except ValueError:
                raise ValidationError({"detail": "Invalid date format."})
        if movie:
            try:
                queryset = queryset.filter(movie=int(movie))
            except ValueError:
                raise ValidationError({"detail": "Invalid movie ID."})
        return queryset.annotate(
            tickets_available=(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
            ) - Count("tickets"))

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user.id)
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
            return queryset
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return self.serializer_class
