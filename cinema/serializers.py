from rest_framework import serializers
from django.db import transaction
from .models import (
    CinemaHall,
    Genre,
    Actor,
    Movie,
    MovieSession,
    Order,
    Ticket
)

# --- Helper Serializers ---

class TicketSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")

class MovieSessionSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(source="cinema_hall.name", read_only=True)
    cinema_hall_capacity = serializers.IntegerField(source="cinema_hall.capacity", read_only=True)
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

# --- Movie Session Details ---

class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    actors = serializers.SlugRelatedField(many=True, read_only=True, slug_field="full_name")

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")

class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = TicketSeatSerializer(source="tickets", many=True, read_only=True)

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )

# --- Orders and Tickets ---

class TicketSerializer(serializers.ModelSerializer):
    # For nested output in Order list
    movie_session = MovieSessionSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

class TicketCreateSerializer(serializers.ModelSerializer):
    # For input during Order creation
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        data = super(TicketCreateSerializer, self).validate(attrs)
        # Check if the seat is already taken for this session
        if Ticket.objects.filter(
            movie_session=attrs["movie_session"],
            row=attrs["row"],
            seat=attrs["seat"]
        ).exists():
            raise serializers.ValidationError({
                "ticket": f"The ticket for row {attrs['row']} and seat {attrs['seat']} is already sold."
            })
        return data

class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = self.initial_data.get("tickets")
            order = Order.objects.create(**validated_data)
            
            if tickets_data:
                for ticket_data in tickets_data:
                    # Validate each ticket individually using the Create Serializer
                    ticket_serializer = TicketCreateSerializer(data=ticket_data)
                    ticket_serializer.is_valid(raise_exception=True)
                    ticket_serializer.save(order=order)
            
            return order
