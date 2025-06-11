from rest_framework import viewsets, permissions, pagination
from django_filters import rest_framework as filters
from rest_framework import serializers


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
    MovieSessionListSerializerWithTicketsAvailable,
    MovieSessionDetailSerializerWithTakenPlaces,
)

from django_filters.rest_framework import DjangoFilterBackend


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


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

class OrderPagination(pagination.PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class MovieFilter(filters.FilterSet):
    genres = filters.CharFilter(field_name='genres__name', lookup_expr='iexact')
    actors = filters.CharFilter(field_name='actors__first_name', lookup_expr='icontains')
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = Movie
        fields = ['genres', 'actors', 'title']


from django_filters import rest_framework as filters

class MovieViewSetWithFilter(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = MovieFilter
    
    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer


class MovieSessionFilter(filters.FilterSet):
    date = filters.DateFilter(field_name="show_time", lookup_expr='date')
    movie = filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = MovieSession
        fields = ['date', 'movie']


class MovieSessionViewSetWithFilter(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = MovieSessionFilter

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializerWithTicketsAvailable
        if self.action == "retrieve":
            return MovieSessionDetailSerializerWithTakenPlaces
        return MovieSessionSerializer



class TakenPlaceSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    seat = serializers.IntegerField()


class MovieSessionDetailSerializerWithTakenPlaces(MovieSessionDetailSerializer):
    taken_places = serializers.SerializerMethodField()

    def get_taken_places(self, obj):
        tickets = obj.tickets.all()
        return [{"row": t.row, "seat": t.seat} for t in tickets]


class MovieSessionListSerializerWithTicketsAvailable(MovieSessionListSerializer):
    tickets_available = serializers.SerializerMethodField()

    def get_tickets_available(self, obj):
        total_capacity = obj.cinema_hall.capacity
        taken_count = obj.tickets.count()
        return total_capacity - taken_count
