from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import Actor, CinemaHall, Genre, Movie, MovieSession, Order
from cinema.serializers import (ActorSerializer, CinemaHallSerializer,
                                GenreSerializer, MovieDetailSerializer,
                                MovieListSerializer, MovieSerializer,
                                MovieSessionDetailSerializer,
                                MovieSessionListSerializer,
                                MovieSessionSerializer, OrderSerializer)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.prefetch_related("movies")
    serializer_class = GenreSerializer

    @staticmethod
    def params_to_ints(qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        if genres := self.request.query_params.get("genres"):
            genre_ids = self.params_to_ints(genres)
            queryset = queryset.filter(id__in=genre_ids)
        if actors := self.request.query_params.get("actors"):
            actor_ids = self.params_to_ints(actors)
            queryset = queryset.filter(movies__actors__id__in=actor_ids)
        if title := self.request.query_params.get("title"):
            queryset = queryset.filter(movies__title__icontains=title)
        return queryset.distinct()


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.select_related().prefetch_related(
        "genres", "actors"
    )
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        if genres := self.request.query_params.get("genres"):
            genre_ids = GenreViewSet.params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)
        if actors := self.request.query_params.get("actors"):
            actor_ids = GenreViewSet.params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)
        if title := self.request.query_params.get("title"):
            queryset = queryset.filter(title__icontains=title)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie", "cinema_hall"
    ).prefetch_related("tickets")
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        if movie_id := self.request.query_params.get("movie"):
            queryset = queryset.filter(movie__id=movie_id)
        if date := self.request.query_params.get("date"):
            queryset = queryset.filter(show_time__date=date)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
