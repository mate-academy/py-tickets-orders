from django.db.models import Prefetch, Count
from django.utils.dateparse import parse_date
from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
)
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
    MovieSessionCreateSerializer,
    MovieWriteSerializer,
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
    genres_prefetch = Prefetch(
        "genres", queryset=Genre.objects.all(), to_attr="prefetched_genres"
    )
    actors_prefetch = Prefetch(
        "actors", queryset=Actor.objects.all(), to_attr="prefetched_actors"
    )

    queryset = Movie.objects.prefetch_related(genres_prefetch, actors_prefetch)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieWriteSerializer

    def get_queryset(self):
        queryset = Movie.objects.prefetch_related(
            self.genres_prefetch, self.actors_prefetch
        )

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres")
        if genres:
            genre_ids = [int(pk) for pk in genres.split(",") if pk.isdigit()]
            queryset = queryset.filter(genres__id__in=genre_ids)

        actors = self.request.query_params.get("actors")
        if actors:
            actor_ids = [int(pk) for pk in actors.split(",") if pk.isdigit()]
            queryset = queryset.filter(actors__id__in=actor_ids)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    tickets_prefetch = Prefetch(
        "tickets",
        queryset=Ticket.objects.select_related("movie_session"),
        to_attr="prefetched_tickets"
    )

    queryset = (
        MovieSession.objects.select_related("movie", "cinema_hall")
        .prefetch_related(tickets_prefetch)
        .annotate(taken_tickets=Count("tickets"))
    )

    def get_queryset(self):
        queryset = (
            MovieSession.objects.select_related(
                "movie", "cinema_hall"
            )
            .prefetch_related(self.tickets_prefetch)
            .annotate(taken_tickets=Count("tickets"))
        )

        date_str = self.request.query_params.get("date")
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(show_time__date=date)

        movie_id = self.request.query_params.get("movie")
        if movie_id and movie_id.isdigit():
            queryset = queryset.filter(movie_id=movie_id)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        elif self.action == "create":
            return MovieSessionCreateSerializer
        return MovieSessionDetailSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "movie_session__movie", "movie_session__cinema_hall"
                    ),
                )
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer
