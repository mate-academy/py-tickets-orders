from django.utils.dateparse import parse_date
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieDetailSerializer,
    MovieSessionSerializer,
    MovieSessionDetailSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
    MovieSessionListWithAvailabilitySerializer,
    MovieListSerializer,
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
        queryset = super().get_queryset().prefetch_related("genres", "actors")

        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            try:
                genre_ids = [
                    int(pk) for pk in genres.split(",") if pk.strip()
                ]
                queryset = queryset.filter(genres__id__in=genre_ids)
            except ValueError:
                pass

        if actors:
            try:
                actor_ids = [
                    int(pk) for pk in actors.split(",") if pk.strip()
                ]
                queryset = queryset.filter(actors__id__in=actor_ids)
            except ValueError:
                pass

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
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()

        movie_id = self.request.query_params.get("movie")
        date_str = self.request.query_params.get("date")

        if movie_id:
            try:
                qs = qs.filter(movie_id=int(movie_id))
            except ValueError:
                pass

        if date_str:
            date_obj = parse_date(date_str)
            if date_obj:
                qs = qs.filter(show_time__date=date_obj)

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        if self.action == "list":
            return MovieSessionListWithAvailabilitySerializer
        return MovieSessionSerializer


class OrderViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                "tickets",
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer
