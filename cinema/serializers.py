from sqlite3 import IntegrityError

from django.db import transaction
from rest_framework import serializers

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket


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

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
        )


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(many=False, read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketForOrderCreateSerializer(TicketSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(queryset=MovieSession.objects.all())

    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

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


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class OrderListSerializer(OrderSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at",)


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketForOrderCreateSerializer(many=True, read_only=False)

    class Meta:
        model = Order
        fields = ("tickets",)

    def validate(self, attrs):
        tickets = attrs["tickets"]
        seats = set()

        for ticket in tickets:
            row = ticket.get('row')
            seat = ticket.get('seat')

            if (row, seat) in seats:
                raise serializers.ValidationError("Duplicate row and seat combination detected.")
            else:
                seats.add((row, seat))

        return attrs

    def create(self, validated_data):
        if self.context['request'].user.is_authenticated:
            with transaction.atomic():
                tickets = validated_data.pop("tickets")
                user = self.context['request'].user
                order = Order.objects.create(user=user, **validated_data)
                for ticket in tickets:
                    try:
                        Ticket.objects.create(order=order, **ticket)
                    except IntegrityError:
                        raise serializers.ValidationError("Duplicate row and seat combination detected.")
                order.save()
            return order
        else:
            raise serializers.ValidationError("User must be authenticated to create an order.")
