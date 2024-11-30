from django.db import transaction
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


class TicketSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs)
        # Validate that the row is correct
        # (not more than cinema_hall capacity)
        row_value = attrs["row"]
        maximal_row_capacity = attrs["movie_session"].cinema_hall.rows
        Ticket.validate_row(
            row_value, maximal_row_capacity, serializers.ValidationError
        )

        # Validate that the seat is correct
        # (not more than cinema_hall capacity)
        seat_value = attrs["seat"]
        maximal_seat_capacity = attrs["movie_session"].cinema_hall.seats_in_row
        Ticket.validate_seat(
            seat_value, maximal_seat_capacity, serializers.ValidationError
        )

        return data

    # def validate(self, attrs):
    #     # attrs is a list of Ticket fields and values
    #     # (movie_session, order, row, seat)
    #     data = super(TicketSerializer, self).validate(attrs)
    #     for ticket_attr_value, ticket_attr_name, cinema_hall_attr_name in [
    #         (attrs["row"], "row", "rows"),  # 3
    #         (attrs["seat"], "seat", "seats_in_row"),  # 2123123
    #     ]:
    #         count_attrs = getattr(
    #             attrs["movie_session"].cinema_hall, cinema_hall_attr_name
    #         )  # find the capacity of cinema hall rows and seats in row
    #         print("seat:", ticket_attr_value)
    #         print("seats in hall:", count_attrs)
    #
    #         if not (1 <= ticket_attr_value <= count_attrs):
    #             raise serializers.ValidationError(
    #                 {
    #                     ticket_attr_name: f"{ticket_attr_name} "
    #                     f"number must be in available range: "
    #                     f"(1, {cinema_hall_attr_name}): "
    #                     f"(1, {count_attrs})"
    #                 }
    #             )
    #
    #     return data

    class Meta:
        model = Ticket
        exclude = ("order",)


class TicketTakenSeatsSerializer(TicketSerializer):
    class Meta(TicketSerializer.Meta):
        exclude = ("id", "movie_session", "order")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    tickets_available = serializers.IntegerField(
        read_only=True
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


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketTakenSeatsSerializer(
        many=True, read_only=True, source="tickets"
    )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")


class TicketListSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(many=False)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True, read_only=False, required=True, allow_empty=False
    )

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            # order data WITHOUT tickets_data to create ORDER
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
