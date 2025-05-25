from datetime import datetime
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    OrderCreateSerializer,
    OrderSerializer,
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
        queryset = Movie.objects.all()
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            title_names = [name.strip() for name in title.split(",")]
            for name in title_names:
                queryset = queryset.filter(title__icontains=name).distinct()
        if genres:
            genres_ids = [
                int(g.strip()) for g in genres.split(",") if g.strip().isdigit()
            ]
            queryset = queryset.filter(genres__id__in=genres_ids).distinct()
        if actors:
            actors_ids = [
                int(a.strip()) for a in actors.split(",") if a.strip().isdigit()
            ]
            queryset = queryset.filter(actors__id__in=actors_ids).distinct()

        return queryset

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
        queryset = MovieSession.objects.all()
        movie = self.request.query_params.get("movie")
        date_str = self.request.query_params.get("date")

        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date)
            except ValueError:
                pass

        if movie:
            try:
                movies_ids = [int(str_id) for str_id in movie.split(",")]
                queryset = queryset.filter(movie__id__in=movies_ids)
            except ValueError:
                pass

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = Order.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session",
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )

        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            title_names = [name.strip() for name in title.split(",")]
            queryset = queryset.filter(
                tickets__movie_session__movie__title__icontains=title_names
            ).distinct()
        if genres:
            genres_name = [genre.strip() for genre in genres.split(",")]
            queryset = queryset.filter(
                tickets__movie_session__movie__genres__name__in=genres_name
            ).distinct()
        if actors:
            actors_name = [actor.strip() for actor in actors.split(",")]
            queryset = queryset.filter(
                tickets__movie_session__movie__actors__first_name__in=actors_name
            ).distinct()

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = OrderSerializer

        if self.action == "list":
            serializer = OrderSerializer
        elif self.action == "create":
            serializer = OrderCreateSerializer
        return serializer
