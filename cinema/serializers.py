from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, F  # Importações adicionadas

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket  # Importações adicionadas


# ... (GenreSerializer, ActorSerializer, CinemaHallSerializer, MovieSerializer, MovieListSerializer, MovieDetailSerializer permanecem os mesmos)

# --- MovieSessionSerializers ---
class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    # NOVO CAMPO: tickets_available (será preenchido no ViewSet)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",
        )


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj: MovieSession):
        taken = Ticket.objects.filter(movie_session=obj).values('row', 'seat')
        return list(taken)


# --- Serializers para Tickets ---
class TicketNestedSerializer(serializers.ModelSerializer):
    # Referencia MovieSessionListSerializer que já foi definida acima
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketWriteSerializer(serializers.ModelSerializer):
    # movie_session deve ser um campo de escrita (PrimaryKeyRelatedField por padrão)
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

        # Validação de range já está no Model.clean()


# --- Serializers para Order ---
class OrderListSerializer(serializers.ModelSerializer):
    # Referencia TicketNestedSerializer que já foi definida acima
    tickets = TicketNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    # tickets é uma lista de TicketWriteSerializer (que espera row, seat, movie_session_id)
    tickets = TicketWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)

    def validate(self, data):
        # Validação de que sessões não acabaram
        session_ids = {
            ticket_info['movie_session']
            for ticket_info in data.get('tickets', [])
            if 'movie_session' in ticket_info  # Garante que o ID está presente
        }

        now = timezone.now()
        past_sessions = MovieSession.objects.filter(
            id__in=session_ids,
            show_time__lt=now
        ).values_list('id', flat=True)

        if past_sessions.exists():
            raise ValidationError(
                f"Não é possível reservar ingressos para as sessões ID: {list(past_sessions)}. Elas já ocorreram."
            )

        return data

    def create(self, validated_data):
        from django.db import transaction  # Importação local para atomic

        ticket_data = validated_data.pop('tickets')
        user = self.context['request'].user

        with transaction.atomic():  # Garante rollback se a criação de um ticket falhar
            order = Order.objects.create(user=user)

            for ticket_info in ticket_data:
                try:
                    Ticket.objects.create(
                        order=order,
                        movie_session_id=ticket_info['movie_session'],  # Usa o ID passado
                        row=ticket_info['row'],
                        seat=ticket_info['seat']
                    )
                except ValidationError as e:
                    # Captura validação do Model (range)
                    raise ValidationError({"tickets": f"Erro ao criar ticket: {e.message_dict}"})
                except Exception as e:
                    # Captura UniqueConstraint (lugar já ocupado) ou outro erro
                    # Para o propósito do exercício, uma mensagem genérica é aceitável se não for falha de FK/Integridade
                    raise ValidationError({"tickets": f"Erro inesperado ao criar ticket: {e}"})

            return order
