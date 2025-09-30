from django.contrib import admin

from .models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
    Ticket,
)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "duration")
    search_fields = ("title",)
    filter_horizontal = ("genres", "actors")


@admin.register(CinemaHall)
class CinemaHallAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "rows", "seats_in_row")


@admin.register(MovieSession)
class MovieSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "movie", "cinema_hall", "show_time")
    list_filter = ("cinema_hall", "movie")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    date_hierarchy = "created_at"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "movie_session", "row", "seat", "order")
    list_filter = ("movie_session",)
    search_fields = ("order__user__username",)


admin.site.register(Genre)
admin.site.register(Actor)
