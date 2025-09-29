from rest_framework import serializers

from cinema.models import (
    Ticket,
    Order,
    MovieSession,
    CinemaHall,
    Movie,
    Actor,
    Genre,
)
from django.db import transaction


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
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )


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
            "actors",
        )


class MovieDetailForSessionSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieDetailForSessionSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )

    def get_taken_places(self, obj):
        tickets = Ticket.objects.filter(movie_session=obj).only("row", "seat")
        return [{"row": t.row, "seat": t.seat} for t in tickets]


class MovieSessionCompactSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
        )


class MovieSessionListWithAvailabilitySerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    tickets_available = serializers.SerializerMethodField()

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

    def get_tickets_available(self, obj):
        total_capacity = obj.cinema_hall.capacity
        taken = Ticket.objects.filter(movie_session=obj).count()
        return max(total_capacity - taken, 0)


class TicketListSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionCompactSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(serializers.ModelSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all()
    )

    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        movie_session = attrs["movie_session"]
        hall = movie_session.cinema_hall
        row = attrs["row"]
        seat = attrs["seat"]

        errors = {}
        if row < 1 or row > hall.rows:
            errors["row"] = (
                f"Row must be within [1..{hall.rows}] for this cinema hall."
            )
        if seat < 1 or seat > hall.seats_in_row:
            errors["seat"] = (
                f"Seat must be within "
                f"[1..{hall.seats_in_row}] for this cinema hall."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        tickets_payload = self.initial_data.get("tickets", [])
        if not tickets_payload:
            raise serializers.ValidationError(
                {
                    "tickets": "This field is required and must "
                               "be a non-empty list."
                }
            )

        by_session = {}
        duplicates = []
        for ticket in tickets_payload:
            try:
                ms_id = int(ticket.get("movie_session"))
                row = int(ticket.get("row"))
                seat = int(ticket.get("seat"))
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    {
                        "tickets":
                            "Each ticket must have integer 'row', 'seat', "
                            "and 'movie_session'."}
                )

            key = (row, seat)
            seen = by_session.setdefault(ms_id, set())
            if key in seen:
                duplicates.append(
                    {"movie_session": ms_id, "row": row, "seat": seat}
                )
            else:
                seen.add(key)

        if duplicates:
            raise serializers.ValidationError(
                {"tickets": {"duplicates": duplicates}}
            )

        conflicts = []
        for ms_id, requested in by_session.items():
            existing = set(
                Ticket.objects.filter(
                    movie_session_id=ms_id, row__in=[r for r, _ in requested]
                ).values_list("row", "seat")
            )
            for pair in requested:
                if pair in existing:
                    conflicts.append(
                        {
                            "movie_session": ms_id,
                            "row": pair[0],
                            "seat": pair[1],
                        }
                    )

            if conflicts:
                raise serializers.ValidationError(
                    {"tickets": {"taken": conflicts}}
                )

        return attrs

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        user = self.context["request"].user
        with transaction.atomic():
            order = Order.objects.create(user=user)
            Ticket.objects.bulk_create(
                [
                    Ticket(
                        order=order,
                        row=ticket_data["row"],
                        seat=ticket_data["seat"],
                        movie_session=ticket_data["movie_session"],
                    )
                    for ticket_data in tickets_data
                ]
            )
        return order
