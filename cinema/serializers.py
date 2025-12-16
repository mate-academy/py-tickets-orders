from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from cinema.models import (Genre,
                           Actor,
                           CinemaHall,
                           Movie,
                           MovieSession,
                           Ticket,
                           Order)


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
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
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
            "tickets_available"
        )

    def get_tickets_available(self, obj):
        return obj.cinema_hall.capacity - obj.taken_places


class MovieSessionOrderSerializer(serializers.ModelSerializer):
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
            "movie_title",
            "show_time",
            "cinema_hall_name",
            "cinema_hall_capacity",
        )


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionOrderSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id", "movie_session", "row", "seat")
        validators = [
            UniqueTogetherValidator(
                queryset=Ticket.objects.all(),
                fields=("movie_session", "row", "seat"),
            )
        ]


class TicketsListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(
        read_only=True
    )

    class Meta:
        model = Ticket
        fields = (
            "id",
            "movie_session",
            "row",
            "seat",
        )


class TicketCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("movie_session", "row", "seat")

    def validate(self, attrs):
        cinema_hall = attrs["movie_session"].cinema_hall

        Ticket.validate_ticket(
            row=attrs["row"],
            seat=attrs["seat"],
            cinema_hall=cinema_hall,
            error_class=serializers.ValidationError,
        )

        return attrs


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketsListSerializer(
        many=True, read_only=True, allow_empty=False)
    tickets_data = TicketCreateSerializer(
        many=True,
        write_only=True,
        allow_empty=False,
        source="tickets"
    )

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets", "tickets_data")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(user=self.context["request"].user)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        return [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in obj.tickets.all()
        ]


class OrderListSerializer(OrderSerializer):
    tickets = TicketSerializer(
        read_only=True, many=True)
