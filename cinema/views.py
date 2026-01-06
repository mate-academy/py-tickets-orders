from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django.db.models import Prefetch

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket,
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
    OrderListSerializer,
    OrdersPagination,
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
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related(
            "genres",
            "actors",
        )
        params = self.request.query_params

        actors = params.get("actors")
        if actors:
            actors_list = [
                int(a.strip())
                for a in actors.strip("[]").split(",")
                if a.strip().isdigit()
            ]

            queryset = queryset.filter(
                actors__id__in=actors_list
            )

        genres = params.get("genres")
        if genres:
            genres_list = [
                int(a.strip())
                for a in genres.strip("[]").split(",")
                if a.strip().isdigit()
            ]

            queryset = queryset.filter(
                genres__id__in=genres_list
            )

        title = params.get("title")
        if title:
            queryset = queryset.filter(
                title__contains=title
            )

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.select_related(
            "movie",
            "cinema_hall",
        )

        params = self.request.query_params

        movie = params.get("movie")
        if movie:
            movie_ids = [
                int(m.strip())
                for m in movie.split(",")
                if m.strip().isdigit()
            ]
            queryset = queryset.filter(movie__id__in=movie_ids)

        date = params.get("date")
        if date:
            queryset = (
                queryset
                .filter(
                    show_time__date=date,
                )
            )

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = OrdersPagination

    def get_queryset(self):
        # Prefetch related objects to avoid N+1
        return (
            Order.objects
            .filter(user=self.request.user)
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "movie_session__cinema_hall",
                        "movie_session__movie"
                    )
                ),
            )
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderCreateSerializer
