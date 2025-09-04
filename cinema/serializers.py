from rest_framework import serializers
from django.db import transaction

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
        fields = ("id", "name", )


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name", )


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity", )


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors", )


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
        fields = ("id", "title", "description", "duration", "genres", "actors", )


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", )


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.SlugRelatedField(
        slug_field="title", source="movie", read_only=True
    )
    cinema_hall_name = serializers.SlugRelatedField(
        slug_field="name", source="cinema_hall", read_only=True
    )
    cinema_hall_capacity = serializers.SlugRelatedField(
        slug_field="capacity", source="cinema_hall", read_only=True
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


class SimpleTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", )


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = SimpleTicketSerializer(
        many=True, read_only=True, source="tickets"
    )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places", )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session", )

    def validate(self, attrs):
        movie_session = attrs["movie_session"]
        hall = movie_session.cinema_hall

        if not (1 <= attrs["row"] <= hall.rows):
            raise serializers.ValidationError({
                "row": f"row number must be in range 1..{hall.rows}"
            })

        if not (1 <= attrs["seat"] <= hall.seats_in_row):
            raise serializers.ValidationError({
                "seat": f"seat number must be in range 1..{hall.seats_in_row}"
            })

        return attrs


class TicketDetailSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at", )

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets", [])
            order = super().create(validated_data)
            for ticket in tickets:
                Ticket.objects.create(**ticket, order=order)
            return order


class OrderDetailSerializer(OrderSerializer):
    tickets = TicketDetailSerializer(
        many=True, read_only=False
    )
