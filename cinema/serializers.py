from rest_framework import serializers
from .models import Movie, MovieSession, Ticket, Order


# ────────────────────────────────
# MOVIE SERIALIZER
# ────────────────────────────────
class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True, slug_field="name", read_only=True
    )
    actors = serializers.SlugRelatedField(
        many=True, slug_field="full_name", read_only=True
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


# ────────────────────────────────
# MOVIE SESSION LIST SERIALIZER
# ────────────────────────────────
class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(source="cinema_hall.name", read_only=True)
    cinema_hall_capacity = serializers.IntegerField(source="cinema_hall.capacity", read_only=True)
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
        taken = Ticket.objects.filter(movie_session=obj).count()
        return obj.cinema_hall.capacity - taken


# ────────────────────────────────
# MOVIE SESSION DETAIL SERIALIZER
# ────────────────────────────────
class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
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

    def get_taken_places(self, obj):
        tickets = Ticket.objects.filter(movie_session=obj)
        return [{"row": t.row, "seat": t.seat} for t in tickets]


# ────────────────────────────────
# TICKET SERIALIZER
# ────────────────────────────────
class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


# ────────────────────────────────
# ORDER SERIALIZER
# ────────────────────────────────
class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user

        order = Order.objects.create(user=user)
        for ticket in tickets_data:
            Ticket.objects.create(order=order, **ticket)

        return order
