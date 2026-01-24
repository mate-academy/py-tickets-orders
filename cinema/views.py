from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, F, Q
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction  # Adicionado para OrderViewSet

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
    OrderListSerializer,  # Adicionado
    OrderCreateSerializer,  # Adicionado
)


# ... (GenreViewSet, ActorViewSet, CinemaHallViewSet permanecem os mesmos)

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    # Remove filter_backends, implementa filtros no get_queryset

    def get_queryset(self):
        queryset = Movie.objects.all()

        # Filtro por título (string) - retorna filmes cujo título contém a string
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)

        # Filtro por gêneros
        genres = self.request.query_params.getlist('genres')  # Pega múltiplos valores
        if genres:
            # Filtra filmes que tenham PELO MENOS um dos gêneros fornecidos
            queryset = queryset.filter(genres__name__in=genres).distinct()

        # Filtro por atores
        actors = self.request.query_params.getlist('actors')  # Pega múltiplos valores
        if actors:
            # Filtra filmes que tenham PELO MENOS um dos atores fornecidos
            queryset = queryset.filter(actors__full_name__in=actors).distinct()

        return queryset.distinct()  # Garante unicidade após M2M joins

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
    # DjangoFilterBackend lida com movie=id. Para date, fazemos manualmente.
    filterset_fields = {'movie': ['exact']}

    def get_queryset(self):
        queryset = MovieSession.objects.all()

        # Filtrar por data (date=YYYY-MM-DD)
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(show_time__date=date_param)

        # Adicionar tickets_available (Requisito)
        queryset = queryset.annotate(
            tickets_sold=Count('tickets', distinct=True)
        ).annotate(
            tickets_available=F('cinema_hall__rows') * F('cinema_hall__seats_in_row') - F('tickets_sold')
        )

        return queryset.order_by('-show_time')  # Mantém ordenação base do model

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


# --- NOVO ViewSet para Order ---
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer  # Para retrieve

    def get_queryset(self):
        # Filtra para retornar apenas os pedidos do usuário autenticado
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'tickets__movie_session__movie',
            'tickets__movie_session__cinema_hall'
        )
