from sqlite3 import IntegrityError

from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    SlugRelatedField,
    CharField,
    IntegerField,
    SerializerMethodField,
)

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket,
)


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name",)


class ActorSerializer(ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name",)


class CinemaHallSerializer(ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity",)


class MovieSerializer(ModelSerializer):
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
    genres = SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    actors = SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = CharField(source="movie.title", read_only=True)
    cinema_hall_name = CharField(
        source="cinema_hall.name",
        read_only=True,
    )
    cinema_hall_capacity = IntegerField(
        source="cinema_hall.capacity",
        read_only=True,
    )
    tickets_available = IntegerField(read_only=True)

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


class TicketSerializer(ModelSerializer):
    movie_session = MovieSessionListSerializer(many=False, read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session",)


class TicketForOrderCreateSerializer(TicketSerializer):
    movie_session = PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all()
    )

    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session",)


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places",)

    @staticmethod
    def get_taken_places(obj):
        taken_places_data = []
        tickets = obj.tickets.all()

        for ticket in tickets:
            taken_places_data.append({
                "row": ticket.row,
                "seat": ticket.seat
            })

        return taken_places_data


class OrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class OrderListSerializer(OrderSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at",)


class OrderCreateSerializer(ModelSerializer):
    tickets = TicketForOrderCreateSerializer(many=True, read_only=False)

    class Meta:
        model = Order
        fields = ("tickets",)

    def validate(self, attrs):
        tickets = attrs["tickets"]
        seats = set()

        for ticket in tickets:
            row = ticket.get("row")
            seat = ticket.get("seat")

            if (row, seat) in seats:
                raise serializers.ValidationError(
                    "Duplicate row and seat combination detected."
                )

            seats.add((row, seat))

        return attrs

    def create_order(self, user, validated_data):
        order = Order.objects.create(user=user, **validated_data)

        self.create_tickets(
            validated_data.pop("tickets"),
            order
        )
        order.save()

        return order

    @staticmethod
    def create_tickets(ticket_data, order):
        for ticket in ticket_data:
            try:
                Ticket.objects.create(order=order, **ticket)
            except IntegrityError:
                raise serializers.ValidationError(
                    "Duplicate row and seat combination detected."
                )

    @transaction.atomic
    def create(self, validated_data):
        if self.context["request"].user.is_authenticated:
            order = self.create_order(
                self.context["request"].user,
                validated_data
            )

            return order

        raise serializers.ValidationError(
            "User must be authenticated to create an order."
        )
