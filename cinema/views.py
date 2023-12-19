from django.db.models import Q, Count, F
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
    MovieListSerializer,
    OrderListSerializer,
    OrderPostSerializer,
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

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("actors", "genres")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors is not None:
            queryset = queryset.filter(
                actors__id=actors
            )

        if genres is not None:
            queryset = queryset.filter(genres__id__in=genres.split(","))

        if title is not None:
            queryset = queryset.filter(title__icontains=title)
        return queryset.distinct()


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
        queryset = self.queryset.prefetch_related("movie", "cinema_hall")
        if self.action == "list":
            queryset = queryset.annotate(
                tickets_count=Count("tickets")
            )

            for item in queryset:
                item.tickets_available = item.cinema_hall.capacity - item.tickets_count

            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")

            if date is not None:
                queryset = queryset.filter(show_time__date=date)

            if movie is not None:
                queryset = queryset.filter(movie=movie)

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(
            pk=self.request.user.pk
        ).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return OrderPostSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
