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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
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
        Order, on_delete=models.CASCADE,
        related_name="tickets"
    )
    row = models.IntegerField()
    seat = models.IntegerField()

    @staticmethod
    def validate_ticket(seat: int, seats: int, row: int, rows: int, error):
        if not (1 <= seat <= seats):
            raise error(
                {"row": f"number must be in available"
                        f"range from 1 until {seats}"}
            )
        if not (1 <= row <= rows):
            raise error(
                {"row": f"number must be in available"
                        f" range from 1 until {rows}"}
            )

    def clean(self):
        seats = self.movie_session.cinema_hall.seats_in_row
        rows = self.movie_session.cinema_hall.rows
        Ticket.validate_ticket(
            seat=self.seat,
            seats=seats,
            row=self.row,
            rows=rows,
            error=ValidationError
        )

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        self.full_clean()
        super(Ticket, self).save(force_insert,
                                 force_update,
                                 using,
                                 update_fields)

    def __str__(self):
        return f"{str(self.movie_session)} " \
               f"(row: {self.row}, seat: {self.seat})"

    class Meta:
        unique_together = ("movie_session", "row", "seat")
