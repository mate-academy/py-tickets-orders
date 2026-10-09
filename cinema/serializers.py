import sqlite3

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
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


class MovieSessionSummarySerializer(MovieSessionSerializer):
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


class MovieSessionListSerializer(MovieSessionSummarySerializer):
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta(MovieSessionSummarySerializer.Meta):
        fields = MovieSessionSummarySerializer.Meta.fields + (
            "tickets_available",
        )


class TicketSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketSeatSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")


class ValidatedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.run_validation(data)
        return super().to_internal_value(data)


class TicketSerializer(serializers.ModelSerializer):
    movie_session = ValidatedPrimaryKeyRelatedField(
        queryset=MovieSession.objects.select_related("cinema_hall"),
        pk_field=serializers.IntegerField(min_value=1, max_value=2 ** 63 - 1),
    )

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")
        read_only_fields = ("id",)

    def validate(self, attrs):
        try:
            Ticket(**attrs).clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        return attrs


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionSummarySerializer(read_only=True)


def _is_ticket_unique_conflict(error):
    table = Ticket._meta.db_table
    return isinstance(error.__cause__, sqlite3.IntegrityError) and str(
        error.__cause__
    ) == (
        "UNIQUE constraint failed: "
        f"{table}.movie_session_id, {table}.row, {table}.seat"
    )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_tickets(self, tickets):
        places = set()
        for ticket in tickets:
            place = (ticket["movie_session"].pk, ticket["row"], ticket["seat"])
            if place in places:
                raise serializers.ValidationError(
                    "A place can only be booked once in the same order."
                )
            places.add(place)
        return tickets

    def create(self, validated_data):
        tickets = validated_data.pop("tickets")
        try:
            with transaction.atomic():
                order = Order.objects.create(**validated_data)
                for ticket in tickets:
                    Ticket.objects.create(order=order, **ticket)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"tickets": error.message_dict}
            ) from error
        except IntegrityError as error:
            if not _is_ticket_unique_conflict(error):
                raise
            raise serializers.ValidationError(
                {"tickets": "One of the selected places is already occupied."}
            ) from error
        return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
