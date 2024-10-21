from rest_framework import viewsets, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters import rest_framework as filters
from rest_framework.views import APIView
from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, CreateOrderSerializer, OrderSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by("id")
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("id")
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all().order_by("id")
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


class OrdersPagination(PageNumberPagination):
    page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrdersPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)


class MovieSessionFilter(filters.FilterSet):
    date = filters.DateFilter(field_name="show_time", lookup_expr="date")
    movie = filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]


class MovieSessionDetailView(APIView):
    def get(self, request, pk):
        movie_session = get_object_or_404(MovieSession, pk=pk)
        taken_places = Ticket.objects.filter(
            movie_session=movie_session).values(
            "row",
            "seat")

        response_data = {
            "id": movie_session.id,
            "show_time": movie_session.show_time,
            "movie": {
                "id": movie_session.movie.id,
                "title": movie_session.movie.title,
                "description": movie_session.movie.description,
                "duration": movie_session.movie.duration,
                "genres": [genre.name
                           for genre in
                           movie_session.movie.genres.all()],
                "actors": [actor.name
                           for actor in
                           movie_session.movie.actors.all()],
            },
            "cinema_hall": {
                "id": movie_session.cinema_hall.id,
                "name": movie_session.cinema_hall.name,
                "rows": movie_session.cinema_hall.rows,
                "seats_in_row": movie_session.cinema_hall.seats_in_row,
                "capacity": movie_session.cinema_hall.capacity,
            },
            "taken_places": list(taken_places),
        }
        return Response(response_data)


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer
