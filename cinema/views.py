from django.db.models.functions import Concat
from django.utils.dateparse import parse_datetime
from django.forms import CharField
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F, CharField, Value

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
    OrderSerializerList,
    OrderSerializerPost
)


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 20


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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            queryset = queryset.annotate(
                actor_full_name=Concat('actors__first_name', Value(' '), 'actors__last_name', output_field=CharField())
            ).filter(
                actor_full_name__icontains=actors
            )
        if genres:
            queryset = queryset.filter(genres__name=genres)
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        movie_id = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")

        if movie_id:
            queryset = queryset.filter(id=movie_id)
        if date:
            date = parse_datetime(date)
            queryset = queryset.filter(show_time__date=date)
        print(date)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )
    serializer_class = OrderSerializerList
    pagination_class = OrderSetPagination

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "create":
            serializer = OrderSerializerPost

        return serializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__cinema_hall",
                "tickets__movie_session__movie"
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
