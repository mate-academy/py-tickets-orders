FIELDS_ACTOR = ("id", "first_name", "last_name", "full_name")
FIELDS_COMMON = ("id", "title", "description", "duration", "genres", "actors")
FIELDS_SHOWTIME = ("id", "show_time", "movie", "cinema_hall")
FIELDS_MOVIE = (
    "id",
    "show_time",
    "movie_title",
    "cinema_hall_name",
    "cinema_hall_capacity",
    "tickets_available"
)
FIELDS_CINEMA_HALL = ("id", "name", "rows", "seats_in_row", "capacity")
FIELDS_GENRE = ("id", "name")
FIELDS_TAKEN = ("row", "seat")
FIELDS_ORDER = ("id", "tickets", "created_at")
FIELDS_TICKET = ("id", "row", "seat", "movie_session")
