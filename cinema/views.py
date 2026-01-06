from rest_framework import viewsets

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
    OrderSerializer,
    OrderListSerializer,
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
    serializer_class = MovieSerializer
    pagination_class = None

    @staticmethod
    def params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = Movie.objects.all()

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres")
        if genres:
            genre_ids = self.params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genre_ids).distinct()

        actors = self.request.query_params.get("actors")
        if actors:
            actor_ids = self.params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actor_ids).distinct()

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
    pagination_class = None

    def get_queryset(self):
        queryset = MovieSession.objects.all()

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(show_time__date=date)

        movie = self.request.query_params.get("movie")
        if movie:
            queryset = queryset.filter(movie_id=movie)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            queryset = Order.objects.filter(user=user)

            if self.action == "list":
                return queryset.prefetch_related(
                    "tickets",
                    "tickets__movie_session__movie",
                    "tickets__movie_session__cinema_hall",
                )

            return queryset

        return Order.objects.none()

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderListSerializer

        if self.action == "create":
            return OrderSerializer

        return OrderListSerializer
