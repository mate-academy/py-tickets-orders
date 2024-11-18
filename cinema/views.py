from django.db.models import Count, F, ExpressionWrapper, IntegerField
from rest_framework import viewsets
from django.utils.dateparse import parse_date
from django.http import request
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
    MovieListSerializer,
    OrderPostSerializer,
    OrderListSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


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
        queryset = self.queryset.prefetch_related(
            "actors",
            "genres"
        )
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    def paginate_queryset(self, queryset):
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors or genres or title:
            return None
        return super().paginate_queryset(queryset)


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
        if self.action == "list":
            capacity_expr = ExpressionWrapper(
                F("cinema_hall__rows") * F("cinema_hall__seats_in_row"),
                output_field=IntegerField())
            queryset = (self.queryset.prefetch_related("tickets", "movie")
                        .annotate(
                tickets_available=capacity_expr - Count("tickets")
            ))
            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")
            if date:
                date = parse_date(date)
                queryset = queryset.filter(show_time__date=date)
            if movie:
                movie_ids = [int(str_id) for str_id in movie.split(",")]
                queryset = queryset.filter(movie_id__in=movie_ids)
            return queryset.distinct()
        elif self.action == "retrieve":
            return self.queryset.prefetch_related(
                "movie",
                "cinema_hall",
                "movie__genres",
                "movie__actors"
            )


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self):
        user = self.request.user
        if self.action in ["list", "retrieve"]:
            return Order.objects.filter(user=user).prefetch_related(
                "tickets",
                "tickets__movie_session",
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderListSerializer
        else:
            return OrderPostSerializer
