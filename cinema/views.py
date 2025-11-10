from rest_framework import viewsets

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
)

from cinema.paginations import OrderPagination

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
    TicketSerializer,
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
    queryset = Movie.objects
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        qs = self.queryset.prefetch_related("genres", "actors")
        params = self.request.GET
        if params:
            if "actors" in params:
                qs = qs.filter(
                    actors__id__in=[
                        int(id_) for id_ in params["actors"].split(",")
                    ]
                )
            if "genres" in params:
                qs = qs.filter(
                    genres__id__in=[
                        int(id_) for id_ in params["genres"].split(",")
                    ]
                )
            if "title" in params:
                qs = qs.filter(
                    title__icontains=params["title"]
                )
        return qs


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects
    serializer_class = MovieSessionSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        qs = self.queryset.select_related("movie")
        date = self.request.GET.get("date")
        movie_ids = self.request.GET.get("movie")
        if date:
            qs = qs.filter(
                show_time__date=date
            )
        if movie_ids:
            qs = qs.filter(
                movie_id__in=[int(id_) for id_ in movie_ids.split(",")]
            )
        return qs


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderPostSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
