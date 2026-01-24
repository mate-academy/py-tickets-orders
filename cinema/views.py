from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated  # Importar permissão
from django.db.models import Count, F, Q  # Importar para filtros e anotações
from django_filters.rest_framework import DjangoFilterBackend  # Importar para filtros

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket  # Importar Order, Ticket

from cinema.serializers import (
    # ... (Serializers existentes)
    OrderListSerializer,  # NOVO
    OrderCreateSerializer,  # NOVO
    MovieSessionListSerializer,  # Para anotação
)


class GenreViewSet(viewsets.ModelViewSet):


# ... (sem alteração)

# ... (ActorViewSet, CinemaHallViewSet - sem alteração)

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {
        'title': 'icontains',  # Filtro por título (substring)
        'genres__name': 'exact',  # Filtro por gênero (exact match no nome)
        'actors__full_name': 'exact',  # Filtro por ator (exact match no full_name)
    }

    # Nota: O DjangoFilterBackend com 'icontains' para char fields pode não funcionar
    # automaticamente como desejado para todos os casos. A implementação manual ou
    # um filtro customizado pode ser mais robusta, mas isso atende ao básico.

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
    filterset_fields = ('movie', 'show_time')  # Permitir filtro por movie e show_time

    def get_queryset(self):
        queryset = super().get_queryset()

        # 1. Filtrar por data (date=YYYY-MM-DD)
        date_param = self.request.query_params.get('date')
        if date_param:
            # Filtra por show_time que começa com a data fornecida
            queryset = queryset.filter(show_time__date=date_param)

        # 2. Filtrar por filme (movie=<id>) - DjangoFilterBackend deve lidar com isso se filterset_fields estiver configurado
        # Se precisar ser manual:
        # movie_param = self.request.query_params.get('movie')
        # if movie_param:
        #    queryset = queryset.filter(movie_id=movie_param)

        # 3. Adicionar tickets_available (Requisito)
        queryset = queryset.annotate(
            tickets_sold=Count('tickets', distinct=True)
        ).annotate(
            tickets_available=F('cinema_hall__rows') * F('cinema_hall__seats_in_row') - F('tickets_sold')
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


# --- NOVO ViewSet para Order ---
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]  # Requer autenticação

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        # Para retrieve, update, partial_update, podemos usar o ListSerializer ou criar um específico
        return OrderListSerializer  # Usando ListSerializer para retrieve

    def get_queryset(self):
        # Filtra para retornar apenas os pedidos do usuário autenticado
        return Order.objects.filter(user=self.request.user).prefetch_related('tickets__movie_session__movie')

    def perform_create(self, serializer):
        # O usuário é definido automaticamente no OrderCreateSerializer.create()
        # e o serializer já tem acesso a self.context['request']
        serializer.save()
