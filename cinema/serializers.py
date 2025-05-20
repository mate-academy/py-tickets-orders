# cinema/serializers.py
from django.db import (
    IntegrityError,
    transaction,
)
from rest_framework import serializers

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
    Ticket,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name",)


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )
    actors = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieRetrieveSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionListSerializer(serializers.ModelSerializer):
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

    def get_tickets_available(self, obj: MovieSession) -> int:
        return obj.cinema_hall.capacity - obj.tickets.count()


class MovieSessionRetrieveSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj: MovieSession) -> list[dict]:
        return [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in obj.tickets.all()
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs: dict) -> dict:
        movie_session = attrs["movie_session"]
        row = attrs["row"]
        seat = attrs["seat"]
        cinema_hall = movie_session.cinema_hall

        if not (1 <= row <= cinema_hall.rows):
            raise serializers.ValidationError(
                {
                    "row": (
                        "Row number must be in available range: "
                        "[1, {}]"
                    ).format(cinema_hall.rows)
                }
            )
        if not (1 <= seat <= cinema_hall.seats_in_row):
            raise serializers.ValidationError(
                {
                    "seat": (
                        "Seat number must be in available range: "
                        "[1, {}]"
                    ).format(cinema_hall.seats_in_row)
                }
            )
        return attrs


class MovieSessionForTicketSerializer(serializers.ModelSerializer):
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


class TicketListSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionForTicketSerializer(
        many=False,
        read_only=True
    )

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at",)

    def validate_tickets(self, tickets_data: list[dict]) -> list[dict]:
        if not tickets_data:
            raise serializers.ValidationError(
                {"tickets": "This list cannot be empty."}
            )
        seen_tickets = set()
        for ticket_data in tickets_data:
            ticket_identifier = (
                ticket_data["movie_session"].id,
                ticket_data["row"],
                ticket_data["seat"]
            )
            if ticket_identifier in seen_tickets:
                message = (
                    "Duplicate ticket for session {}, "
                    "row {}, seat {} in this order."
                ).format(
                    ticket_data["movie_session"].id,
                    ticket_data["row"],
                    ticket_data["seat"]
                )
                raise serializers.ValidationError({"tickets": message})
            seen_tickets.add(ticket_identifier)
        return tickets_data

    def create(self, validated_data: dict) -> Order:
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                try:
                    Ticket.objects.create(order=order, **ticket_data)
                except IntegrityError:
                    message = (
                        "Ticket for session {}, "
                        "row {}, seat {} is already taken."
                    ).format(
                        ticket_data["movie_session"].id,
                        ticket_data["row"],
                        ticket_data["seat"]
                    )
                    raise serializers.ValidationError({"tickets": message})
            return order


class MovieSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")
        read_only_fields = ("id",)


class MovieWriteSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(), many=True, required=False
    )
    actors = serializers.PrimaryKeyRelatedField(
        queryset=Actor.objects.all(), many=True, required=False
    )

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")
        read_only_fields = ("id",)

    def create(self, validated_data: dict) -> Movie:
        genres_data = validated_data.pop("genres", [])
        actors_data = validated_data.pop("actors", [])
        movie = Movie.objects.create(**validated_data)
        movie.genres.set(genres_data)
        movie.actors.set(actors_data)
        return movie

    def update(self, instance: Movie, validated_data: dict) -> Movie:
        genres_data = validated_data.pop("genres", None)
        actors_data = validated_data.pop("actors", None)

        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get(
            "description", instance.description
        )
        instance.duration = validated_data.get("duration", instance.duration)
        instance.save()

        if genres_data is not None:
            instance.genres.set(genres_data)
        if actors_data is not None:
            instance.actors.set(actors_data)
        return instance
