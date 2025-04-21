from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.db.models import UniqueConstraint


class CinemaHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.IntegerField()
    genres = models.ManyToManyField(Genre)
    actors = models.ManyToManyField(Actor)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class MovieSession(models.Model):
    show_time = models.DateTimeField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    cinema_hall = models.ForeignKey(CinemaHall, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-show_time"]

    def __str__(self):
        return self.movie.title + " " + str(self.show_time)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    movie_session = models.ForeignKey(
        MovieSession, on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )
    row = models.IntegerField()
    seat = models.IntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["movie_session", "row", "seat"],
                name="unique_ticket"
            )
        ]

    @staticmethod
    def validate_seat(row, seat, movie_session, error_to_raise):
        seat_validators = {
            "row": row,
            "seat": seat
        }
        hall_limits = {
            "row": movie_session.cinema_hall.rows,
            "seat": movie_session.cinema_hall.seats_in_row
        }

        for attr, value in seat_validators.items():
            max_value = hall_limits[attr]
            if not (1 <= value <= max_value):
                raise error_to_raise({
                    attr: f"{attr} must be between 1 and {max_value}"
                })

    def clean(self):
        self.validate_seat(
            self.row,
            self.seat,
            self.movie_session,
            ValidationError
        )

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        super(Ticket, self).save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    def __str__(self):
        return (
            f"{str(self.movie_session)} (row: {self.row}, seat: {self.seat})"
        )
