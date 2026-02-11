from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket,
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


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    tickets_available = serializers.SerializerMethodField()
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
            "tickets_available",
        )

    def get_tickets_available(self, obj):
        return obj.cinema_hall.capacity - obj.tickets.count()


class MovieSessionDetailSerializer(MovieSessionSerializer):
    taken_places = serializers.SerializerMethodField()
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )

    def get_taken_places(self, obj):
        tickets = obj.tickets.all()
        return [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in tickets
        ]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def get_movie_session(self, obj):
        return {
            "id": obj.movie_session.id,
            "show_time": obj.movie_session.show_time,
            "movie_title": obj.movie_session.movie.title,
            "cinema_hall_name": obj.movie_session.cinema_hall.name,
            "cinema_hall_capacity": obj.movie_session.cinema_hall.capacity,
        }


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        if Ticket.objects.filter(
                movie_session=attrs["movie_session"],
                row=attrs["row"],
                seat=attrs["seat"],
        ).exists():
            raise serializers.ValidationError(
                "Seat already taken."
            )
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(
            user=self.context["request"].user
        )

        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)

        return order
