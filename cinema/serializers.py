from django.db import transaction
from django.db.models import Count, F
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
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )

    # tickets_available = serializers.IntegerField(source="cinema_hall.capacity", read_only=True)
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

    # DRY work correctly
    # def validate(self, attrs):
    #     data = super(TicketSerializer, self).validate(attrs)
    #     Ticket.validate_seat(
    #         attrs["movie_sessions"].cinema_hall.capacity(),
    #         serializers.ValidationError
    #     )
    #     return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketDetailSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketDetailSerializer(
        source="tickets",
        many=True,
        read_only=True
    )
    # How to change field name in Django REST Framework
    # location = serializers.CharField(source='other_fields')

    # class Meta:
    #     model = Park
    #     fields = ('other_fields', 'location')
    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )



class TicketListSerializer(TicketSerializer):
    # Add detail information about movie session
    movie_session = MovieSessionListSerializer(many=False, read_only=True)# тут read_only=True вже не буде заважати додавати нові квитки


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")# забрала можливість вибирати поточного користувача

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        # Потім створюємо замовлення без інформації про квитки
        order = Order.objects.create(**validated_data)
        # Для кожної окремої інформації про квитки у загальній інформації про квитки
        for ticket_data in tickets_data:
            # Створюю новий квиток, вказую, що замовлення в цього квитка
            # таке як у створеного вище замовлення
            # order = Order.objects.create(**validated_data)
            # та далі передаю розпаковані дані про квиток
            Ticket.objects.create(order=order, **ticket_data)
        # Далі повертаю замовлення
        return order


    # def create(self, validated_data):
    #
    #     with transaction.atomic():
    #         tickets_data = validated_data.pop("tickets")
    #         order = Order.objects.create(**validated_data)
    #
    #         for ticket_data in tickets_data:
    #             Ticket.objects.create(order=order, **ticket_data)
    #         return order

#
class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=False)# read_only=True
