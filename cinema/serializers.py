from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, F

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket


# ... (GenreSerializer, ActorSerializer, CinemaHallSerializer, MovieSerializer, MovieListSerializer, MovieDetailSerializer permanecem os mesmos)

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors"
        )


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
        taken = Ticket.objects.filter(movie_session=obj).values('row', 'seat').order_by('row', 'seat')
        return list(taken)


# --- Serializers para Tickets ---
class TicketNestedSerializer(serializers.ModelSerializer):
    # Usa string para referência circular/ordem
    movie_session = "MovieSessionListSerializer"

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketWriteSerializer(serializers.ModelSerializer):
    # Define explicitamente para garantir que aceita o ID de MovieSession
    movie_session = serializers.PrimaryKeyRelatedField(queryset=MovieSession.objects.all())

    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


# --- Serializers para Order ---
class OrderListSerializer(serializers.ModelSerializer):
    # Usa string para referência circular/ordem
    tickets = TicketNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at"
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)

    def validate(self, data):
        # Coleta todos os IDs de sessão referenciados no payload
        session_ids = {
            ticket_info['movie_session']
            for ticket_info in data.get('tickets', [])
            if 'movie_session' in ticket_info
        }

        now = timezone.now()
        # Verifica se alguma sessão já ocorreu
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
        from django.db import IntegrityError  # Importa para capturar duplicatas
        ticket_data = validated_data.pop('tickets')
        user = self.context['request'].user

        # Coleta todas as posições para checar duplicidade no payload e DB
        new_tickets_info = []
        for ticket_info in ticket_data:
            # Garante que movie_session é o objeto buscado pelo PK RF no validate
            session_id = ticket_info['movie_session'].id
            new_tickets_info.append((session_id, ticket_info['row'], ticket_info['seat']))

        # Checa duplicatas no payload (opcional mas bom)
        if len(new_tickets_info) != len(set(new_tickets_info)):
            raise ValidationError({"tickets": "Há ingressos duplicados (mesma sessão/fileira/assento) no seu pedido."})

        with transaction.atomic():
            order = Order.objects.create(user=user)

            for session_id, row, seat in new_tickets_info:
                try:
                    # Cria o ticket, full_clean no save() chama model.clean() (range check)
                    Ticket.objects.create(
                        order=order,
                        movie_session_id=session_id,
                        row=row,
                        seat=seat
                    )
                except IntegrityError:
                    # Captura falha em unique_together ("movie_session", "row", "seat")
                    raise ValidationError(
                        {"tickets": f"Assento ({row}, {seat}) já está ocupado na sessão {session_id}."})
                except ValidationError as e:
                    # Captura falha de model.clean() (range check)
                    raise ValidationError({"tickets": f"Erro na validação de assento: {e.message_dict}"})
                except Exception as e:
                    # Captura qualquer outro erro inesperado
                    raise ValidationError({"tickets": "Erro inesperado ao reservar assento."})

            return order
