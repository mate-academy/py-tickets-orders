from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from cinema.models import (Genre,
                           Actor,
                           CinemaHall,
                           Movie,
                           MovieSession,
                           Order,
                           Ticket)


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


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        validators = UniqueTogetherValidator("row", "seat")
        model = Ticket
        fields = "__all__"


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(many=False)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")


class OrderCreateSerializer(OrderSerializer):
    tickets = TicketCreateSerializer(many=True, read_only=False)

    def create(self, validated_data):
        tickets = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)
        for ticket in tickets:
            Ticket.objects.create(order=order, **ticket)
        return order


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketSerializer(many=True,
                                    source="tickets",
                                    read_only=True)

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")
