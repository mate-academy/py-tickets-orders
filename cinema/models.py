from django.contrib.messages import error
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


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

    @staticmethod
    def validate_row_seat(
            movie_session: MovieSession,
            ticket_attr_value: int,
            ticket_attr_name: str,
            cinema_hall_attr_name: str,
            error_to_raise: error
    ):
        max_attr_value = getattr(
            movie_session.cinema_hall, cinema_hall_attr_name
        )
        if not (1 <= ticket_attr_value <= max_attr_value):
            raise error_to_raise(
                {
                    ticket_attr_name: f"{ticket_attr_name} "
                                      f"number must be in available range: "
                                      f"(1, {max_attr_value})"
                }
            )

    def clean(self):
        Ticket.validate_row_seat(
            self.movie_session,
            self.row,
            "row",
            "rows",
            ValidationError)
        Ticket.validate_row_seat(
            self.movie_session,
            self.seat,
            "seat",
            "seats_in_row",
            ValidationError
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return (
            f"{str(self.movie_session)} (row: {self.row}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("movie_session", "row", "seat")
