from django.db.models import Count, F
from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
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

    def get_queryset(self):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        queryset = Movie.objects.all()

        for param_name, param_value in (
            ("actors", actors),
            ("genres", genres),
        ):
            if param_value:
                try:
                    ids = [int(value) for value in param_value.split(",")]
                except ValueError:
                    raise ValidationError(
                        {param_name: "Provide comma-separated integer IDs."}
                    )

                if any(id_ <= 0 for id_ in ids):
                    raise ValidationError(
                        {param_name: "IDs must be positive integers."}
                    )

                queryset = queryset.filter(**{f"{param_name}__id__in": ids})

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

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

    def get_queryset(self):
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")
        result = {}
        if date:
            result["show_time__date"] = date
        if movie:
            try:
                movie_id = int(movie)

            except ValueError:
                raise ValidationError({"movie": "Invalid movie ID."})

            if movie_id <= 0:
                raise ValidationError({"movie": "Movie ID must be positive."})
            else:
                result["movie__id"] = movie_id

        queryset = MovieSession.objects.filter(**result)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("movie", "cinema_hall")

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderAPIview(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericAPIView
):
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderListSerializer
        else:
            return OrderSerializer
