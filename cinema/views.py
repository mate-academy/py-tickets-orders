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
    serializer_class = MovieSerializer
    pagination_class = None

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
        titles = self.request.query_params.get("title")

        if genres:
            genres_list = [genre.strip() for genre in genres.split(",")]
            qs = qs.filter(genres__id__in=genres_list)

        if actors:
            actor_ids = [actor_id.strip() for actor_id in actors.split(",") if
                         actor_id.strip().isdigit()]
            if actor_ids:
                qs = qs.filter(actors__id__in=actor_ids)

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
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            self.pagination_class = None
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        qs = self.queryset
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if movie:
            qs = qs.filter(movie__id=movie.strip())

        if date:
            qs = qs.filter(show_time__date=date.strip())

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
            self.pagination_class = None
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
