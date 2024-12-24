from django.db.models import Q, Count, F
from django.db.models.functions import TruncDate
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
    OrderListSerializer,
    TicketSerializer,
    OrderCreateSerializer,
    MovieSessionCreateSerializer,
    TicketListSerializer,
    TicketTakenSeatsSerializer, ActorCreateSerializer, ActorListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return ActorListSerializer
        if self.action == "create":
            return ActorCreateSerializer
        return ActorSerializer


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
        queryset = self.queryset.prefetch_related()

        actors = self.request.query_params.get("actors")
        if actors:
            actor_values = actors.split(",")
            query = Q()
            for value in actor_values:
                if value.isdigit():
                    query |= Q(id=value)
                else:
                    query |= Q(actors__first_name__icontains=value) | Q(
                        actors__last_name__icontains=value
                    )
            queryset = queryset.filter(query)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(
                title__icontains=title
            )

        genres = self.request.query_params.get("genres")
        if genres:
            genres_list = genres.split(",")
            print("Genres list:", genres_list)
            queryset = queryset.filter(
                genres__id__in=genres_list
            )

        return queryset.distinct()


from django.db.models import F, Count
from django.db.models.functions import TruncDate


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()

    def get_queryset(self):
        queryset = self.queryset.select_related(
            "movie", "cinema_hall"
        ).prefetch_related("tickets")

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        # Фильтрация по дате
        if date:
            queryset = queryset.annotate(date=TruncDate("show_time")).filter(
                date=date)

        # Фильтрация по фильму
        if movie:
            queryset = queryset.filter(movie=movie)

        # Аннотация доступных мест
        queryset = queryset.annotate(
            capacity=F("cinema_hall__rows") * F("cinema_hall__seats_in_row"),
            tickets_available=F("capacity") - Count("tickets")
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        if self.action == "create":
            return MovieSessionCreateSerializer
        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.prefetch_related("movie_session")

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "retrieve":
            return TicketSerializer

        return TicketSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
