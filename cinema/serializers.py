from rest_framework import serializers
from cinema.models import (
    Genre, Actor,
    CinemaHall, Movie,
    MovieSession, Ticket, Order
)


class MovieSessionListSerializer(serializers.ModelSerializer):
    tickets_available = serializers.SerializerMethodField()

    def get_tickets_available(self, obj):
        total_tickets = obj.cinema_hall.capacity
        sold_tickets = obj.tickets.count()
        return total_tickets - sold_tickets

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


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def validate(self, data):
        movie_session = data.get("movie_session")
        if not movie_session:
            raise serializers.ValidationError(
                "Необходимо указать сеанс фильма."
            )
        row = data.get("row")
        seat = data.get("seat")
        # Проверка на занятость места
        if Ticket.objects.filter(
            movie_session=movie_session, row=row, seat=seat
        ).exists():
            raise serializers.ValidationError("Это место уже занято.")
        # Проверка допустимости номера ряда
        if not (1 <= row <= movie_session.cinema_hall.rows):
            raise serializers.ValidationError("Недопустимый номер ряда.")
        # Проверка допустимости номера места
        if not (1 <= seat <= movie_session.cinema_hall.seats_in_row):
            raise serializers.ValidationError("Недопустимый номер места.")
        return data


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(user=self.context["request"].user)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all()
    )
    actors = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Actor.objects.all()
    )

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def get_genres(self, obj):
        return [genre.name for genre in obj.genres.all()]

    def get_actors(self, obj):
        return [
            f"{actor.first_name} {actor.last_name}"
            for actor in obj.actors.all()
        ]


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


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        tickets = obj.tickets.all()
        return [{"row": ticket.row, "seat": ticket.seat} for ticket in tickets]
