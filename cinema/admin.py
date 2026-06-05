from django.contrib import admin

from cinema.models import (
    Genre,
    Actor,
    Movie,
    CinemaHall,
    MovieSession,
    Order,
    Ticket,
)

admin.site.register(Genre)
admin.site.register(Actor)
admin.site.register(Movie)
admin.site.register(CinemaHall)
admin.site.register(MovieSession)
admin.site.register(Order)
admin.site.register(Ticket)
