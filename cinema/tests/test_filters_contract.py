from datetime import datetime

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from cinema.models import Actor, CinemaHall, Genre, Movie, MovieSession


MOVIES_URL = "/api/cinema/movies/"
MOVIE_SESSIONS_URL = "/api/cinema/movie_sessions/"


class MovieFiltersContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.drama = Genre.objects.create(name="Drama")
        self.comedy = Genre.objects.create(name="Comedy")
        self.science_fiction = Genre.objects.create(name="Science fiction")
        self.kate = Actor.objects.create(
            first_name="Kate", last_name="Winslet"
        )
        self.leonardo = Actor.objects.create(
            first_name="Leonardo", last_name="DiCaprio"
        )
        self.tom = Actor.objects.create(first_name="Tom", last_name="Hanks")
        self.matching = self.create_movie(
            "Titanic Revisited",
            [self.drama, self.comedy],
            [self.kate, self.leonardo],
        )
        self.genre_only = self.create_movie(
            "Titanic Comedy", [self.comedy], [self.tom]
        )
        self.actor_only = self.create_movie(
            "Other Story", [self.science_fiction], [self.kate]
        )
        self.other_title = self.create_movie(
            "Epic Voyage", [self.drama], [self.leonardo]
        )
        self.unrelated = self.create_movie(
            "Quiet Life", [self.science_fiction], [self.tom]
        )

    @staticmethod
    def create_movie(title, genres, actors):
        movie = Movie.objects.create(
            title=title, description="Description", duration=100
        )
        movie.genres.set(genres)
        movie.actors.set(actors)
        return movie

    def assert_movie_ids(self, response, movies):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertCountEqual(
            [movie["id"] for movie in response.data],
            [movie.id for movie in movies],
        )

    def test_ids_within_each_filter_are_combined_with_or(self):
        filters = (
            (
                {"genres": f"{self.drama.id},{self.comedy.id}"},
                [self.matching, self.genre_only, self.other_title],
            ),
            (
                {"actors": f"{self.kate.id},{self.leonardo.id}"},
                [self.matching, self.actor_only, self.other_title],
            ),
        )
        for parameters, movies in filters:
            with self.subTest(parameters=parameters):
                self.assert_movie_ids(
                    self.client.get(MOVIES_URL, parameters), movies
                )

    def test_different_filter_parameters_are_combined_with_and(self):
        response = self.client.get(
            MOVIES_URL,
            {
                "genres": self.comedy.id,
                "actors": self.kate.id,
                "title": "tItAnIc",
            },
        )
        self.assert_movie_ids(response, [self.matching])

    def test_multiple_matching_genres_and_actors_do_not_duplicate_movies(self):
        response = self.client.get(
            MOVIES_URL,
            {
                "genres": f"{self.drama.id},{self.comedy.id}",
                "actors": f"{self.kate.id},{self.leonardo.id}",
            },
        )
        self.assert_movie_ids(response, [self.matching, self.other_title])

    def test_title_matches_a_case_insensitive_substring(self):
        cases = (
            ("tItAnIc", [self.matching, self.genre_only]),
            ("anic R", [self.matching]),
            ("Missing title", []),
        )
        for title, movies in cases:
            with self.subTest(title=title):
                self.assert_movie_ids(
                    self.client.get(MOVIES_URL, {"title": title}), movies
                )

    def test_unknown_valid_ids_return_an_empty_list(self):
        for parameter in ("genres", "actors"):
            with self.subTest(parameter=parameter):
                response = self.client.get(MOVIES_URL, {parameter: 999999})
                self.assert_movie_ids(response, [])

    def test_malformed_id_lists_return_bad_request(self):
        for parameter in ("genres", "actors"):
            for value in ("invalid", "1,invalid", "1,,2", "1.5"):
                with self.subTest(parameter=parameter, value=value):
                    response = self.client.get(
                        MOVIES_URL, {parameter: value}
                    )
                    self.assertEqual(
                        response.status_code, status.HTTP_400_BAD_REQUEST
                    )

    def test_ids_outside_big_auto_field_range_return_bad_request(self):
        for parameter in ("genres", "actors"):
            with self.subTest(parameter=parameter):
                response = self.client.get(
                    MOVIES_URL, {parameter: str(2 ** 63)}
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

    def test_empty_parameters_do_not_filter_movies(self):
        response = self.client.get(
            MOVIES_URL, {"genres": "", "actors": "", "title": ""}
        )
        self.assert_movie_ids(
            response,
            [
                self.matching,
                self.genre_only,
                self.actor_only,
                self.other_title,
                self.unrelated,
            ],
        )


class MovieSessionFiltersContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.movie = Movie.objects.create(
            title="Titanic", description="Description", duration=100
        )
        self.other_movie = Movie.objects.create(
            title="Other Movie", description="Description", duration=90
        )
        self.hall = CinemaHall.objects.create(
            name="White", rows=5, seats_in_row=10
        )
        self.morning = self.create_session(self.movie, "2022-09-02T09:00:00")
        self.late_evening = self.create_session(
            self.movie, "2022-09-02T23:59:00"
        )
        self.other_movie_session = self.create_session(
            self.other_movie, "2022-09-02T14:00:00"
        )
        self.previous_day = self.create_session(
            self.movie, "2022-09-01T23:59:00"
        )
        self.next_day = self.create_session(self.movie, "2022-09-03T00:00:00")

    def create_session(self, movie, show_time):
        return MovieSession.objects.create(
            movie=movie,
            cinema_hall=self.hall,
            show_time=datetime.fromisoformat(show_time),
        )

    def assert_session_ids(self, response, sessions):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertCountEqual(
            [session["id"] for session in response.data],
            [session.id for session in sessions],
        )

    def test_date_matches_the_entire_calendar_day(self):
        response = self.client.get(
            MOVIE_SESSIONS_URL, {"date": "2022-09-02"}
        )
        self.assert_session_ids(
            response,
            [self.morning, self.late_evening, self.other_movie_session],
        )

    def test_movie_filter_matches_only_the_requested_movie(self):
        response = self.client.get(
            MOVIE_SESSIONS_URL, {"movie": self.other_movie.id}
        )
        self.assert_session_ids(response, [self.other_movie_session])

    def test_date_and_movie_filters_are_combined_with_and(self):
        for date in ("2022-09-02", "2022-09-2"):
            with self.subTest(date=date):
                response = self.client.get(
                    MOVIE_SESSIONS_URL,
                    {"date": date, "movie": self.movie.id},
                )
                self.assert_session_ids(
                    response, [self.morning, self.late_evening]
                )

    def test_unknown_valid_movie_id_returns_an_empty_list(self):
        response = self.client.get(MOVIE_SESSIONS_URL, {"movie": 999999})
        self.assert_session_ids(response, [])

    def test_malformed_movie_ids_and_dates_return_bad_request(self):
        parameters = (
            {"movie": "invalid"},
            {"movie": "1,2"},
            {"movie": "1.5"},
            {"date": "invalid"},
            {"date": "2022-02-30"},
            {"date": "2022-13-02"},
            {"date": "2022-09-02T09:00:00"},
        )
        for values in parameters:
            with self.subTest(parameters=values):
                response = self.client.get(MOVIE_SESSIONS_URL, values)
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

    def test_movie_id_outside_big_auto_field_range_returns_bad_request(self):
        response = self.client.get(
            MOVIE_SESSIONS_URL, {"movie": str(2 ** 63)}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_parameters_do_not_filter_sessions(self):
        response = self.client.get(
            MOVIE_SESSIONS_URL, {"date": "", "movie": ""}
        )
        self.assert_session_ids(
            response,
            [
                self.morning,
                self.late_evening,
                self.other_movie_session,
                self.previous_day,
                self.next_day,
            ],
        )
