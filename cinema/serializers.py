# ... (imports)

# ... (GenreSerializer até MovieDetailSerializer)

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


# ... (MovieSessionSerializer)

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
        # Corrigido Q000 e E501
        taken = Ticket.objects.filter(movie_session=obj).values("row", "seat").order_by("row", "seat")
        return list(taken)


# --- Serializers para Tickets ---
class TicketNestedSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)  # Ajustado de string para objeto

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "movie_session"
        )


class TicketWriteSerializer(serializers.ModelSerializer):
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
        for ticket_info in data.get("tickets", []):
            session_id = ticket_info["movie_session"].id
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
        ticket_data = validated_data.pop("tickets")
        user = self.context["request"].user

        new_tickets_info = []
        for ticket_info in ticket_data:
            session_id = ticket_info["movie_session"].id
            new_tickets_info.append((session_id, ticket_info["row"], ticket_info["seat"]))

        if len(new_tickets_info) != len(set(new_tickets_info)):
            raise ValidationError({"tickets": "Há ingressos duplicados no seu pedido."})

        # Checa conflito com DB
        existing_tickets = Ticket.objects.filter(
            movie_session_id__in={s[0] for s in new_tickets_info},
            row__in={s[1] for s in new_tickets_info},
            seat__in={s[2] for s in new_tickets_info}
        ).values_list("movie_session_id", "row", "seat")

        conflicts = set(existing_tickets) & set(new_tickets_info)
        if conflicts:
            raise ValidationError({"tickets": "Assentos já ocupados."})

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
                except DjangoValidationError as e:
                    raise ValidationError({"tickets": f"Erro de validação de assento: {e.message_dict}"})
                except Exception:
                    raise ValidationError({"tickets": "Erro inesperado ao reservar assento."})

            return order
