from django.utils import timezone
from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order,
)


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
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    duration = serializers.IntegerField(required=True)
    genres = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
    )
    actors = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
    )

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

    def create(self, validated_data):
        genres = validated_data.pop("genres")
        actors = validated_data.pop("actors")
        movie = Movie.objects.create(**validated_data)
        movie.genres.set(genres)
        movie.actors.set(actors)
        return movie

    def update(self, instance, validated_data):
        genres = validated_data.pop("genres", None)
        actors = validated_data.pop("actors", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if genres is not None:
            instance.genres.set(genres)
        if actors is not None:
            instance.actors.set(actors)
        instance.save()
        return instance

    def validate(self, attrs):
        errors = {}
        if not attrs.get("title"):
            errors["title"] = "This field is required."
        if not attrs.get("description"):
            errors["description"] = "This field is required."
        if attrs.get("duration") in (None, ""):
            errors["duration"] = "This field is required."
        if "genres" not in attrs or not attrs["genres"]:
            errors["genres"] = "This field is required."
        if "actors" not in attrs or not attrs["actors"]:
            errors["actors"] = "This field is required."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    actors = serializers.SerializerMethodField()

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

    def get_actors(self, obj):
        return [
            f"{actor.first_name} {actor.last_name}"
            for actor in obj.actors.all()
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

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


class MovieSessionSerializer(serializers.ModelSerializer):
    movie = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(),
        required=True,
        allow_null=False,
    )
    cinema_hall = serializers.PrimaryKeyRelatedField(
        queryset=CinemaHall.objects.all(),
        required=True,
        allow_null=False,
    )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")

    def validate_show_time(self, value):
        if value is not None and timezone.is_naive(value):
            value = timezone.make_aware(
                value,
                timezone.get_current_timezone(),
            )
        return value


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(
        source="movie.title",
        read_only=True,
    )
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True,
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True,
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
            "tickets_available",
        )

    def get_tickets_available(self, obj):
        return obj.cinema_hall.capacity - obj.tickets.count()


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = serializers.SerializerMethodField()
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )

    def get_movie(self, obj):
        return {
            "id": obj.movie.id,
            "title": obj.movie.title,
            "description": obj.movie.description,
            "duration": obj.movie.duration,
            "genres": [g.name for g in obj.movie.genres.all()],
            "actors": [
                f"{a.first_name} {a.last_name}" for a in obj.movie.actors.all()
            ],
        }

    def get_taken_places(self, obj):
        return [
            {"row": t.row, "seat": t.seat}
            for t in obj.tickets.all()
        ]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        exists = Ticket.objects.filter(
            movie_session=attrs["movie_session"],
            row=attrs["row"],
            seat=attrs["seat"],
        ).exists()
        if exists:
            raise serializers.ValidationError("This seat is already taken.")
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        user = self.context["request"].user
        order = Order.objects.create(user=user)
        Ticket.objects.bulk_create(
            [Ticket(order=order, **td) for td in tickets_data]
        )
        return order
