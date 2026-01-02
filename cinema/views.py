from django.db.models import Q, Count, ExpressionWrapper, F, IntegerField
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
    OrderWriteSerializer,
)


class ParamsMixin:
    @staticmethod
    def _params_to_ints(qs):
        """Convert a list of string IDs to a list of integers"""
        if not qs:
            return []
        return [int(str_int) for str_int in qs.split(",")]


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


class MovieViewSet(viewsets.ModelViewSet, ParamsMixin):
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
        query = Q()

        actors = self._params_to_ints(
            self.request.query_params.get("actors")
        )
        if actors:
            query &= Q(actors__in=actors)

        genres = self._params_to_ints(
            self.request.query_params.get("genres")
        )
        if genres:
            query &= Q(genres__in=genres)

        title = self.request.query_params.get("title")
        if title:
            query &= Q(title__icontains=title)

        if query:
            queryset = queryset.filter(query).distinct()

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet, ParamsMixin):
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
        query = Q()

        date_param = self.request.query_params.get("date")
        if date_param:
            query &= Q(show_time__date=date_param)

        movie_param = self.request.query_params.get("movie")
        if movie_param:
            try:
                movie_id = int(movie_param)
                query &= Q(movie_id=movie_id)
            except ValueError:
                return MovieSession.objects.none()

        if query:
            queryset = queryset.filter(query).distinct()

        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall")
                .annotate(
                    tickets_sold=Count("tickets"),
                    tickets_available=ExpressionWrapper(
                        F("cinema_hall__rows") * F(
                            "cinema_hall__seats_in_row") - F("tickets_sold"),
                        output_field=IntegerField(),
                    )
                )
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "create":
            serializer_class = OrderWriteSerializer

        return serializer_class

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall"
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
