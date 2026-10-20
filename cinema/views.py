from django.db.models import Count, F, QuerySet
from rest_framework import mixins, serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)

from cinema.serializers import (
    OrderSerializer,
    OrderListSerializer,
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        for parameter in ("genres", "actors"):
            value = self.request.query_params.get(parameter)
            if value:
                try:
                    ids = [int(item) for item in value.split(",")]
                except ValueError as error:
                    raise ValidationError(
                        {parameter: "Expected comma-separated integer IDs."}
                    ) from error
                queryset = queryset.filter(**{f"{parameter}__id__in": ids})
        title = self.request.query_params.get("title")
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
    pagination_class = None
    queryset = MovieSession.objects.select_related(
        "movie", "cinema_hall"
    ).annotate(
        tickets_available=(
            F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
            - Count("tickets")
        )
    )
    serializer_class = MovieSessionSerializer

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        if date:
            date = serializers.DateField().run_validation(date)
            queryset = queryset.filter(show_time__date=date)
        if movie:
            movie = serializers.IntegerField().run_validation(movie)
            queryset = queryset.filter(movie_id=movie)
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "movie__genres", "movie__actors", "tickets"
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        ).order_by("-created_at", "-id")

    def get_serializer_class(self) -> type[serializers.ModelSerializer]:
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer: OrderSerializer) -> None:
        serializer.save(user=self.request.user)
