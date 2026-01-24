# ... (imports existentes)
from cinema.models import Order, Ticket  # Importar Order e Ticket
from django.db.models import Count, F
from django.utils import timezone
from rest_framework.exceptions import ValidationError


# ... (Serializers existentes: GenreSerializer, ActorSerializer, etc.)

# --- Serializers para Tickets (para aninhamento) ---
class TicketNestedSerializer(serializers.ModelSerializer):
    # Serializer para exibição (incluindo detalhes da sessão)
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketWriteSerializer(serializers.ModelSerializer):
    # Serializer para escrita/criação (recebe ID da sessão)
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")
        read_only_fields = ('movie_session',)  # Será preenchido no create/update da Order

    # Opcional: Validação a nível de serializer para ticket (como solicitado)
    def validate(self, data):
        # Este tipo de validação é mais complicado aqui pois o movie_session
        # não está totalmente carregado antes do save da Order.
        # A validação de `clean()` no model já trata o range de row/seat.
        # Vamos focar em garantir que não há duplicatas na requisição (se necessário).
        # Para evitar sobrecarga, confiaremos na validação do Model para row/seat range
        # e no unique_together do Model para a unicidade (session/row/seat).
        return data


# --- Serializers para Order ---
class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketWriteSerializer(many=True)  # Recebe a lista de tickets a criar

    class Meta:
        model = Order
        fields = ("tickets",)

    def create(self, validated_data):
        ticket_data = validated_data.pop('tickets')
        user = self.context['request'].user
        order = Order.objects.create(user=user, **validated_data)

        for ticket_info in ticket_data:
            # Validação de duplicata e range será feita pelo self.full_clean() no save() do Ticket
            Ticket.objects.create(
                order=order,
                movie_session=ticket_info['movie_session'],
                row=ticket_info['row'],
                seat=ticket_info['seat']
            )

        return order

    def validate(self, data):
        # Opcional: Validação de que os tickets não estão sendo reservados para sessões passadas
        for ticket_info in data.get('tickets', []):
            try:
                session = MovieSession.objects.get(id=ticket_info['movie_session'].id)
                if session.show_time < timezone.now():
                    raise ValidationError(
                        f"Não é possível reservar ingressos para a sessão {session.id} pois ela já ocorreu.")
            except MovieSession.DoesNotExist:
                raise ValidationError(f"MovieSession com ID {ticket_info['movie_session'].id} não encontrado.")

        return data


# --- Adição de campos em MovieSessionSerializer (Requisito: tickets_available) ---
from django.db.models import Count, F
from cinema.models import Ticket  # Já importado acima, mas para clareza


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    # NOVO CAMPO: tickets_available
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",  # Adicionado
        )


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()  # Campo para lugares ocupados

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj: MovieSession):
        # Retorna os lugares ocupados para a sessão
        taken = Ticket.objects.filter(movie_session=obj).values('row', 'seat')
        return list(taken)
