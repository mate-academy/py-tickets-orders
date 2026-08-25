from django.db import transaction
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
        fields = ("id", "show_time", "movie", "cinema_hall")


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
    movie = MovieListSerializer(read_only=True)
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
        return obj.tickets.values("row", "seat")


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
        movie_session = attrs["movie_session"]

        row = attrs["row"]
        seat = attrs["seat"]

        if not 1 <= row <= movie_session.cinema_hall.rows:
            raise serializers.ValidationError(
                {
                    "row": (
                        f"Row must be in range "
                        f"1-{movie_session.cinema_hall.rows}"
                    )
                }
            )

        if not 1 <= seat <= movie_session.cinema_hall.seats_in_row:
            raise serializers.ValidationError(
                {
                    "seat": (
                        f"Seat must be in range "
                        f"1-{movie_session.cinema_hall.seats_in_row}"
                    )
                }
            )

        if Ticket.objects.filter(
            movie_session=movie_session,
            row=row,
            seat=seat,
        ).exists():
            raise serializers.ValidationError(
                "This place is already taken."
            )

        return attrs


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )
        read_only_fields = ("created_at",)

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")

        with transaction.atomic():
            order = Order.objects.create(
                user=self.context["request"].user,
                **validated_data,
            )

            for ticket_data in tickets_data:
                Ticket.objects.create(
                    order=order,
                    **ticket_data,
                )

        return order


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(
        many=True,
        read_only=True,
    )
