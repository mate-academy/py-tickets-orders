from django.db.models import QuerySet, Q
from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from rest_framework.serializers import Serializer

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderReadSerializer,
    OrderWriteSerializer
)


class MovieWriteSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all()
    )
    actors = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Actor.objects.all()
    )

    class Meta:
        model = Movie
        fields = ("title", "description", "duration", "genres", "actors")


class NoPagination(PageNumberPagination):
    page_size = None


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
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres")
        if genres:
            genres_list = [g.strip() for g in genres.split(",")]
            if all(g.isdigit() for g in genres_list):
                queryset = queryset.filter(
                    genres__id__in=genres_list
                ).distinct()
            else:
                queryset = queryset.filter(
                    genres__name__in=genres_list
                ).distinct()

        actors = self.request.query_params.get("actors")
        if actors:
            actors_list = [a.strip() for a in actors.split(",")]

            actor_filter = Q()
            for actor in actors_list:
                if actor.isdigit():
                    actor_filter |= Q(actors__id=actor)
                else:
                    parts = actor.split()
                    if len(parts) == 2:
                        actor_filter |= Q(
                            actors__first_name__icontains=parts[0],
                            actors__last_name__icontains=parts[1]
                        )
                    else:
                        actor_filter |= Q(
                            actors__first_name__icontains=actor
                        ) | Q(
                            actors__last_name__icontains=actor
                        )
            queryset = queryset.filter(actor_filter).distinct()
        return queryset

    def get_serializer_class(self) -> type[Serializer]:
        if self.action == "list":
            return MovieListSerializer
        elif self.action == "retrieve":
            return MovieDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return MovieWriteSerializer
        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)
        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie_id=movie)
        return queryset

    def get_serializer_class(self) -> type[Serializer]:
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderWriteSerializer
        return OrderReadSerializer
