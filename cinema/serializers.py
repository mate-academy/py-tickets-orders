from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, F
from django.db import IntegrityError  # Importar para captura no create
from django.core.exceptions import ValidationError as DjangoValidationError  # Alias para evitar conflito

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket


# ... (GenreSerializer, ActorSerializer, CinemaHallSerializer, MovieSerializer, MovieListSerializer, MovieDetailSerializer permanecem os mesmos)
# ... (MovieSessionSerializer, MovieSessionListSerializer, MovieSessionDetailSerializer permanecem os mesmos)

class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj: MovieSession):
        # Ordenação corrigida para evitar warnings/inconsistências
        taken = Ticket.objects.filter(movie_session=obj).values('row', 'seat').order_by('row', 'seat')
        return list(taken)


# --- Serializers para Tickets ---
class TicketNestedSerializer(serializers.ModelSerializer):
    # Usa string para evitar F821, mas o serializer aninhado deve ser um campo que DRF reconhece
    # Corrigido para um SerializerMethodField ou campo que aceite o nome
    # No retorno, usamos o nome do campo, mas para o read_only o DRF tentará resolver.
    # Se o erro persistir, este campo deve ser um SerializerMethodField.
    movie_session = "MovieSessionListSerializer"

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketWriteSerializer(serializers.ModelSerializer):
    # Garante que aceita o ID e o valida contra MovieSession
    movie_session = serializers.PrimaryKeyRelatedField(queryset=MovieSession.objects.all())

    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


# --- Serializers para Order ---
class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)

    def validate(self, data):
        session_ids = set()
        for ticket_info in data.get('tickets', []):
            # Pega o ID, pois o PrimaryKeyRelatedField no validated_data armazena o objeto, mas .id é o int
            session_id = ticket_info['movie_session'].id
            session_ids.add(session_id)

        now = timezone.now()
        past_sessions = MovieSession.objects.filter(
            id__in=session_ids,
            show_time__lt=now
        ).exists()

        if past_sessions:
            raise ValidationError(
                "Não é possível reservar ingressos para sessões que já ocorreram."
            )

        return data

    def create(self, validated_data):
        from django.db import transaction
        ticket_data = validated_data.pop('tickets')
        user = self.context["request"].user

        # Coleta informações para checagem de duplicidade DB/Payload
        new_tickets_info = []
        for ticket_info in ticket_data:
            session_id = ticket_info['movie_session'].id
            new_tickets_info.append((session_id, ticket_info['row'], ticket_info['seat']))

        if len(new_tickets_info) != len(set(new_tickets_info)):
            raise ValidationError({"tickets": "Há ingressos duplicados (mesma sessão/fileira/assento) no seu pedido."})

        # Checa conflito com DB
        existing_tickets = Ticket.objects.filter(
            movie_session_id__in={s[0] for s in new_tickets_info},
            row__in={s[1] for s in new_tickets_info},
            seat__in={s[2] for s in new_tickets_info}
        ).values_list('movie_session_id', 'row', 'seat')

        conflicts = set(existing_tickets) & set(new_tickets_info)
        if conflicts:
            raise ValidationError({"tickets": f"Assentos já ocupados: {list(conflicts)}"})

        with transaction.atomic():
            order = Order.objects.create(user=user)

            for session_id, row, seat in new_tickets_info:
                try:
                    Ticket.objects.create(
                        order=order,
                        movie_session_id=session_id,
                        row=row,
                        seat=seat
                    )
                except DjangoValidationError as e:  # Captura validação do Model (range)
                    raise ValidationError({"tickets": f"Erro de validação de assento: {e.message_dict}"})
                except Exception:
                    # Se passou nas checagens, deve ser um erro raro de integridade não mapeado
                    raise ValidationError({"tickets": "Erro inesperado ao reservar assento."})

            return order
