from django.db import transaction
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
        fields = ["id", "name"]


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name", "full_name"]

    def get_full_name(self, obj: Actor) -> str:
        return f"{obj.first_name} {obj.last_name}"


class CinemaHallSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = CinemaHall
        fields = ["id", "name", "rows", "seats_in_row", "capacity"]


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    actors = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id", "title", "description", "duration", "genres", "actors",
        ]

    def get_actors(self, obj: Movie) -> list[str]:
        return [
            f"{actor.first_name} {actor.last_name}"
            for actor in obj.actors.all()
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id", "title", "description", "duration", "genres", "actors",
        ]


class MovieWriteSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
    )
    actors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Actor.objects.all(),
    )

    class Meta:
        model = Movie
        fields = [
            "id", "title", "description", "duration", "genres", "actors",
        ]


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(
        source="movie.title",
        read_only=True,
    )
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True,
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True,
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = MovieSession
        fields = [
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",
        ]


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = [
            "id", "show_time", "movie", "cinema_hall", "taken_places",
        ]

    def get_taken_places(self, obj: MovieSession) -> list[dict]:
        return list(
            obj.tickets.order_by("row", "seat").values("row", "seat")
        )


class MovieSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ["id", "show_time", "movie", "cinema_hall"]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all(),
    )

    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "movie_session"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        movie_session = attrs.get(
            "movie_session",
            self.instance.movie_session if self.instance else None,
        )
        row = attrs.get("row", self.instance.row if self.instance else None)
        seat = attrs.get("seat", self.instance.seat if self.instance else None)

        if movie_session is not None:
            hall = movie_session.cinema_hall

            if row is not None and not 1 <= row <= hall.rows:
                raise serializers.ValidationError({
                    "row": f"Row must be between 1 and {hall.rows}.",
                })

            if seat is not None and not 1 <= seat <= hall.seats_in_row:
                raise serializers.ValidationError({
                    "seat": (
                        f"Seat must be between 1 and {hall.seats_in_row}."
                    ),
                })

        return attrs


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_tickets(self, tickets):
        seen_places = set()

        for ticket in tickets:
            place = (
                ticket["movie_session"].id,
                ticket["row"],
                ticket["seat"],
            )

            if place in seen_places:
                raise serializers.ValidationError(
                    "The same place cannot be booked twice in one order."
                )

            seen_places.add(place)

            if Ticket.objects.filter(
                movie_session=ticket["movie_session"],
                row=ticket["row"],
                seat=ticket["seat"],
            ).exists():
                raise serializers.ValidationError(
                    f"Row {ticket['row']}, seat {ticket['seat']} "
                    "is already booked for this session."
                )

        return tickets

    @transaction.atomic
    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)

        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)

        return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
