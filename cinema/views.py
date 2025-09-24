from django.db.models import Q, F, Count, ExpressionWrapper, IntegerField
from rest_framework import viewsets

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)
from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
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
        qs = super().get_queryset()
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        titles = self.request.query_params.get("titles")

        if genres:
            genres_list = [genre.strip() for genre in genres.split(",")]
            qs = qs.filter(genres__name__in=genres_list)

        if actors:
            actors_list = [actor.strip() for actor in actors.split(",")]
            qs = qs.filter(actors__first_name__in=actors_list)

        if titles:
            titles_list = [title.strip() for title in titles.split(",")]
            q_obj = Q()
            for title in titles_list:
                q_obj |= Q(title__icontains=title)
            qs = qs.filter(q_obj)

        return qs.distinct()


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
        qs = self.queryset
        data = self.request.query_params.get("data")
        movie = self.request.query_params.get("movie")

        if movie:
            qs = qs.filter(movie__id=movie.strip())

        if data:
            qs = qs.filter(show_time=data.strip())

        if self.action == "list":
            qs = qs.annotate(
                tickets_available=ExpressionWrapper(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets"),
                    output_field=IntegerField(),
                )
            )
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer

    def get_queryset(self):
        qs = self.queryset.prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )
        user = self.request.user
        if user.is_authenticated:
            return qs.filter(user=user)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
