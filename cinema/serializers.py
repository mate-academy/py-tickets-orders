from django.db import transaction
from rest_framework import serializers

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
        fields = ("id",
                  "title",
                  "description",
                  "duration",
                  "genres",
                  "actors")


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(many=True,
                                          read_only=True,
                                          slug_field="name")
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    tickets_taken = serializers.IntegerField(read_only=True,
                                             source="tickets.count")

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
            "tickets_taken",
        )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id",
                  "title",
                  "description",
                  "duration",
                  "genres",
                  "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title",
                                        read_only=True)
    cinema_hall_name = (serializers.CharField
                        (source="cinema_hall.name", read_only=True))
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    tickets_available = (serializers.IntegerField
                         (read_only=True))

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
    movie = MovieListSerializer(many=False,
                                read_only=True)
    cinema_hall = CinemaHallSerializer(many=False,
                                       read_only=True)

    class Meta:
        model = MovieSession
        fields = ("id",
                  "show_time",
                  "movie",
                  "cinema_hall")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["taken_places"] = [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in instance.tickets.all()
        ]
        return representation


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id",
                  "row",
                  "seat",
                  "movie_session",
                  "order")

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs)
        cinema_hall = attrs["movie_session"].cinema_hall
        Ticket.validate_position(
            attrs["row"],
            cinema_hall.rows,
            "row",
            serializers.ValidationError
        )
        Ticket.validate_position(
            attrs["seat"], cinema_hall.seats_in_row,
            "seat",
            serializers.ValidationError
        )
        return data


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True,
                               read_only=False,
                               allow_empty=False)

    class Meta:
        model = Order
        fields = ("id",
                  "created_at",
                  "user",
                  "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True,
                                   read_only=True)
