from rest_framework import serializers

from cinema.models import (Genre, Actor,
                           CinemaHall, Movie,
                           MovieSession, Order, Ticket)


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


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(source="cinema_hall.name",
                                             read_only=True)
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True)
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
        total_capacity = obj.cinema_hall.capacity
        taken_tickets = obj.tickets.count()
        return total_capacity - taken_tickets


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    @staticmethod
    def get_taken_places(obj):
        return obj.tickets.values("row", "seat")


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(serializers.ModelSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all()
    )

    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, write_only=True)
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data, **kwargs):
        user = kwargs.get("user") or self.context["request"].user
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(user=user)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order
