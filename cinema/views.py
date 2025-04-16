from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (Genre, Actor,
                           CinemaHall, Movie,
                           MovieSession,
                           Order,
                           Ticket)
from django.db.models import (Prefetch,
                              Count, F,
                              ExpressionWrapper,
                              IntegerField)
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


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related("genres", "actors")
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
        queryset = (
            MovieSession.objects
            .select_related("movie", "cinema_hall")
            .annotate(
                tickets_available=ExpressionWrapper(
                    F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row") - Count("tickets"),
                    output_field=IntegerField()
                )
            )
        )
        movie = self.request.query_params.get("movie")
        date = self.request.query_params.get("date")
        if movie:
            movies_ids = [int(str_id) for str_id in movie.split(",")]
            queryset = queryset.filter(movie__id__in=movies_ids)
        if date:
            queryset = queryset.filter(show_time__date=date)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            Prefetch(
                "tickets",
                queryset=Ticket.objects.select_related(
                    "movie_session__movie",
                    "movie_session__cinema_hall"
                )
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
