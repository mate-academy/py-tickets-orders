from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, F
from django_filters.rest_framework import DjangoFilterBackend

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket

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
    OrderCreateSerializer,
)


# ... (GenreViewSet, ActorViewSet, CinemaHallViewSet)

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    # REMOVIDO filter_backends e filterset_fields

    def get_queryset(self):
        queryset = Movie.objects.all()

        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)

        # Filtro por gêneros (assumindo múltiplos parâmetros ?genres=X&genres=Y)
        genres = self.request.query_params.getlist('genres')
        if genres:
            queryset = queryset.filter(genres__name__in=genres).distinct()

        # Filtro por atores (assumindo múltiplos parâmetros ?actors=X&actors=Y)
        actors = self.request.query_params.getlist('actors')
        if actors:
            queryset = queryset.filter(actors__full_name__in=actors).distinct()

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
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {'movie': ['exact']}

    def get_queryset(self):
        queryset = MovieSession.objects.all()

        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(show_time__date=date_param)

        # Adicionar tickets_available (Requisito)
        queryset = queryset.annotate(
            tickets_sold=Count('tickets', distinct=True)
        ).annotate(
            tickets_available=F('cinema_hall__capacity') - F('tickets_sold')
        )

        return queryset.order_by("-show_time")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


# ... (OrderViewSet)
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall",
        )
