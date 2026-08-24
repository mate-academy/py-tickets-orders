from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    MovieListSerializer, OrderSerializer,
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


class OrderSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 10

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors")
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def paginate_queryset(self, queryset):
        if self.request.query_params.get("page") and len(self.request.query_params) > 1:
            return None
        return super().paginate_queryset(queryset)

    def get_queryset(self):
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        queryset = self.queryset
        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            actors = [int(actor) for actor in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors)
        if genres:
            genres = [int(genre) for genre in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres)
        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def paginate_queryset(self, queryset):
        if self.request.query_params.get("page") and len(self.request.query_params) > 1:
            return None
        return super().paginate_queryset(queryset)


    def get_queryset(self):
        date = self.request.query_params.get("date")
        movies_id = self.request.query_params.get("movie")
        print(movies_id)
        queryset = self.queryset
        if date:
            date = parse_date(date)
            queryset = queryset.filter(show_time__date=date)
        if movies_id:
            movies_id = [int(movie_id) for movie_id in movies_id.split(",")]
            queryset = queryset.filter(movie_id__in=movies_id)
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall",
    )
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)
