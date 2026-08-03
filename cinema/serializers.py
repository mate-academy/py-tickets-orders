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
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name",
        )


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "capacity",
        )


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
        many=True,
        read_only=True,
        slug_field="name",
    )
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
        )


class MovieSessionListSerializer(MovieSessionSerializer):
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
        taken_tickets = Ticket.objects.filter(
            movie_session_id=obj.id,
        ).count()

        return obj.cinema_hall.capacity - taken_tickets


class TakenPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = TakenPlaceSerializer(
        source="tickets",
        many=True,
        read_only=True,
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


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "movie_session",
        )

    def validate(self, attrs):
        row = attrs["row"]
        seat = attrs["seat"]
        movie_session = attrs["movie_session"]
        cinema_hall = movie_session.cinema_hall

        if not 1 <= row <= cinema_hall.rows:
            raise serializers.ValidationError(
                {
                    "row": (
                        f"Row must be in available range: "
                        f"(1, {cinema_hall.rows})"
                    )
                }
            )

        if not 1 <= seat <= cinema_hall.seats_in_row:
            raise serializers.ValidationError(
                {
                    "seat": (
                        f"Seat must be in available range: "
                        f"(1, {cinema_hall.seats_in_row})"
                    )
                }
            )

        if Ticket.objects.filter(
            movie_session=movie_session,
            row=row,
            seat=seat,
        ).exists():
            raise serializers.ValidationError(
                {
                    "seat": (
                        "This seat is already taken for "
                        "the selected movie session."
                    )
                }
            )

        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["movie_session"] = (
            MovieSessionListSerializer(
                instance.movie_session,
                context=self.context,
            ).data
        )

        return representation


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_at",
        )

    def validate_tickets(self, tickets):
        if not tickets:
            raise serializers.ValidationError(
                "At least one ticket must be provided."
            )

        selected_places = set()

        for ticket in tickets:
            place = (
                ticket["movie_session"].id,
                ticket["row"],
                ticket["seat"],
            )

            if place in selected_places:
                raise serializers.ValidationError(
                    "The same ticket was provided more than once."
                )

            selected_places.add(place)

        return tickets

    @transaction.atomic
    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user

        order = Order.objects.create(
            user=user,
            **validated_data,
        )

        for ticket_data in tickets_data:
            Ticket.objects.create(
                order=order,
                **ticket_data,
            )

        return order
