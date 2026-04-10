from django.db import transaction
from rest_framework import serializers

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
        many=True,
        read_only=True,
        slug_field="name")
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
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
        source="cinema_hall.name",
        read_only=True)
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


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        queryset = (obj.tickets.all()
                    .values("row", "seat")
                    .order_by("row", "seat"))
        return list(queryset)


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer()

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(TicketSerializer):
    row = serializers.IntegerField()
    seat = serializers.IntegerField()
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all()
    )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def validate(self, data):
        return data

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user
        with transaction.atomic():
            order = Order.objects.create(user=user, **validated_data)
            for ticket in tickets_data:
                movie_session = ticket["movie_session"]
                if Ticket.objects.filter(
                    movie_session=movie_session,
                        row=ticket["row"],
                        seat=ticket["seat"]
                ).exists():
                    raise serializers.ValidationError("Place already taken")
                Ticket.objects.create(order=order, **ticket)
        return order

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        created = rep.pop("created_at", None)
        rep["tickets"] = TicketSerializer(
            instance.tickets.all(),
            many=True).data
        if created is not None:
            rep["created_at"] = created
        return rep
