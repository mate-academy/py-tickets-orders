from datetime import datetime

from django.db.models import Q, Count, F
from rest_framework import viewsets
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
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    TicketSerializer,
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
        queryset = self.queryset

        title = self.request.query_params.get("title")

        if title:
            queryset = queryset.filter(title__icontains=title)

        genres = self.request.query_params.get("genres")

        if genres:
            genres_list = [g.strip() for g in genres.split(",")]

            q_objects = Q()
            for genre in genres_list:
                if genre.isdigit():
                    q_objects |= Q(genres__id=int(genre))
                else:
                    q_objects |= Q(genres__name__icontains=genre)

            queryset = queryset.filter(q_objects).distinct()

        actors = self.request.query_params.get("actors")

        if actors:
            actors_list = [a.strip() for a in actors.split(",")]

            q_objects = Q()
            for actor in actors_list:
                if actor.isdigit():
                    q_objects |= Q(actors__id=int(actor))
                else:
                    q_objects |= (
                        Q(actors__first_name__icontains=actor)
                        | Q(actors__last_name__icontains=actor)
                    )
            queryset = queryset.filter(q_objects).distinct()

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("genres", "actors")

        return queryset


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
        queryset = self.queryset

        movie = self.request.query_params.get("movie")

        if movie:
            if movie.isdigit():
                queryset = queryset.filter(movie__id=int(movie))
            else:
                queryset = queryset.filter(movie__title__icontains=movie)

        date = self.request.query_params.get("date")

        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=parsed_date)

            except ValueError:
                pass

        if self.action == "list":
            queryset = queryset.select_related(
                "cinema_hall",
                "movie").annotate(
                tickets_available=F(
                    "cinema_hall__rows"
                ) * F("cinema_hall__seats_in_row") - Count("tickets"))
        elif self.action == "retrieve":
            queryset = (queryset.select_related(
                "movie",
                "cinema_hall"
            ).prefetch_related("tickets"))
        return queryset


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "movie_session__cinema_hall",
                "movie_session__movie"
            )
        return queryset


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 1000


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
