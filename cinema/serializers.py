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
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionReadSerializer(MovieSessionSerializer):
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


class MovieSessionListSerializer(MovieSessionReadSerializer):
    tickets_available = serializers.SerializerMethodField()

    @staticmethod
    def get_tickets_available(obj):
        return obj.cinema_hall.capacity - obj.tickets.count()

    class Meta(MovieSessionReadSerializer.Meta):
        fields = MovieSessionReadSerializer.Meta.fields + (
            "tickets_available",
        )


class TakenPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TakenPlaceSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )


class TicketReadSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionReadSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "movie_session",
        )


class OrderReadSerializer(serializers.ModelSerializer):
    tickets = TicketReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at"
        )


class TicketWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            "row",
            "seat",
            "movie_session",
        )

    def validate(self, attrs):
        movie_session = attrs["movie_session"]
        row = attrs["row"]
        seat = attrs["seat"]
        cinema_hall = movie_session.cinema_hall

        errors = {}
        if not 1 <= row <= cinema_hall.rows:
            errors["row"] = (
                f"Row must be in range from 1 to {cinema_hall.rows}."
            )
        if not 1 <= seat <= cinema_hall.seats_in_row:
            errors["seat"] = (
                "Seat must be in range from 1 to "
                f"{cinema_hall.seats_in_row}."
            )
        if errors:
            raise serializers.ValidationError(errors)

        if Ticket.objects.filter(
            movie_session=movie_session,
            row=row,
            seat=seat,
        ).exists():
            raise serializers.ValidationError(
                "This seat is already taken for the selected movie session."
            )

        return attrs


class OrderWriteSerializer(serializers.ModelSerializer):
    tickets = TicketWriteSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = (
            "tickets",
        )

    @staticmethod
    def validate_tickets(tickets):
        places = [
            (ticket["movie_session"].id, ticket["row"], ticket["seat"])
            for ticket in tickets
        ]
        if len(places) != len(set(places)):
            raise serializers.ValidationError(
                "An order cannot contain duplicate tickets."
            )
        return tickets

    @transaction.atomic
    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order
