from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession
from cinema.models import Order, Ticket


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


class MovieSessionListSerializer(MovieSessionSerializer):
    tickets_available = serializers.IntegerField(read_only=True)
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
            "tickets_available",
        )


class TakenPlaceSerializer(serializers.ModelSerializer):
    """Expose occupied seat coordinates without order or user data."""

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
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")


class TicketSerializer(serializers.ModelSerializer):
    """Validate ticket coordinates against the selected hall."""

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        ticket = Ticket(**attrs)
        try:
            ticket.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        return attrs


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    """Create an order and all of its tickets in one transaction."""

    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data: dict[str, Any]) -> Order:
        tickets = validated_data.pop("tickets")
        try:
            with transaction.atomic():
                order = Order.objects.create(**validated_data)
                for ticket in tickets:
                    Ticket.objects.create(order=order, **ticket)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"tickets": error.messages}
            ) from error
        except IntegrityError as error:
            raise serializers.ValidationError(
                {"tickets": "One or more seats are already booked."}
            ) from error
        return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
