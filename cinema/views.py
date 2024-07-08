from rest_framework import viewsets, serializers
from django.db.models import Value, Count, F
from django.db.models.functions import Concat
from django.utils.dateparse import parse_date

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
    OrderListSerializer
)
from rest_framework.pagination import PageNumberPagination


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

    def get_queryset(self):
        queryset = super().get_queryset()
        
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres:
            queryset = queryset.filter(genres__name__icontains=genres)
        if actors:
            queryset = queryset.annotate(full_name=Concat('actors__first_name', Value(' '), 'actors__last_name')).filter(full_name__icontains=actors)

        
        return queryset.distinct()

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
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall")
                .annotate(tickets_available=F("cinema_hall__seats_in_row") - Count("tickets"))
        ).order_by("id")
        date_str = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")
        if date_str:
            date = parse_date(date_str)
            print(date)
            if date:
                queryset = queryset.filter(show_time=date)

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset.distinct()
    
class OrderPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 20
    
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__movie_session__cinema_hall")

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self): 	
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
