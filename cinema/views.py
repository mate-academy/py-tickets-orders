from django.db.models import F
from django.db.models.aggregates import Count
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
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
from cinema.utils import (
    params_to_ints,
    QueryParamsToQuerySet,
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        queryset = (
            QueryParamsToQuerySet(queryset, self.request)
            .apply(
                parameter_name="actors",
                queryset_lookup="actors__id__in",
                param_transformer=params_to_ints,
            )
            .apply(
                parameter_name="genres",
                queryset_lookup="genres__id__in",
                param_transformer=params_to_ints,
            )
            .apply(
                parameter_name="title",
                queryset_lookup="title__icontains",
            )
            .queryset
        )

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

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
                QueryParamsToQuerySet(queryset, self.request)
                .apply(
                    parameter_name="date",
                    queryset_lookup="show_time__date",
                )
                .apply(
                    parameter_name="movie",
                    queryset_lookup="movie_id",
                    param_transformer=int,
                )
                .queryset
            )

            queryset = queryset.prefetch_related("tickets").annotate(
                tickets_available=F("cinema_hall__seats_in_row")
                * F("cinema_hall__rows")
                - Count("tickets"),
            )

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session"
            ).filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
