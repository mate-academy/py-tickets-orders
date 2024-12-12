from rest_framework import viewsets
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.paginations import OrderPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, OrderCreateSerializer,
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
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__in=actors_ids)
        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__in=genres_ids)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall")
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            date = self.request.query_params.get("date")
            movies = self.request.query_params.get("movie")

            if date:
                queryset = queryset.filter(show_time__date=date,)

            if movies:
                movies_ids = [int(str_id) for str_id in movies.split(",")]
                queryset = queryset.filter(movie_id__in=movies_ids)

            queryset = (
                queryset
                .select_related("cinema_hall",)
                .prefetch_related("tickets")
            ).order_by("id")

            for obj in queryset:
                obj.tickets_available = (
                    obj.cinema_hall.capacity - len(obj.tickets.all())
                )
        return queryset


class OrderSessionViewSet(viewsets.ModelViewSet):
    pagination_class = OrderPagination
    queryset = Order.objects.prefetch_related("tickets__movie_session")
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer
