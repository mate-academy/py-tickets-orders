from rest_framework import serializers
from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieListSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
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


class TicketDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketDetailSerializer(
        many=True,
        read_only=True,
        source="tickets"
    )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    class TicketSerializer(serializers.ModelSerializer):
        class Meta:
            model = Ticket
            fields = ("id", "row", "seat", "movie_session")

    class TicketListSerializer(TicketSerializer):
        movie_session = MovieSessionListSerializer(many=False, read_only=True)

    class OrderSerializer(serializers.ModelSerializer):
        tickets = TicketSerializer(read_only=False, many=True)

        class Meta:
            model = Order
            fields = ("id", "tickets", "created_at")

        def create(self, validated_data):
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order

        def validate(self, attrs):
            for ticket in attrs["tickets"]:
                cinema_hall = ticket["movie_session"].cinema_hall
                row = ticket["row"]
                seat = ticket["seat"]

                self.validate_ticket_position(
                    value=row,
                    max_value=cinema_hall.rows,
                    name="Row"
                )
                self.validate_ticket_position(
                    value=seat,
                    max_value=cinema_hall.seats_in_row,
                    name="Seat"
                )
            return attrs

        @staticmethod
        def validate_ticket_position(
                value: int,
                max_value: int,
                name: str
        ):
            if not (1 <= value <= max_value):
                raise serializers.ValidationError(
                    {
                        f"{name} must be in available range: "
                        f"(1, {max_value})"
                    }
                )


tSerializer(OrderSerializer):
    tickets = TicketListSerializer(read_only=True, many=True)
