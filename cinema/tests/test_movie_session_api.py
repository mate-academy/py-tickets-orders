import datetime

from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import Movie, Genre, Actor, MovieSession, CinemaHall


class MovieSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        drama = Genre.objects.create(
            name="Drama",
        )
        comedy = Genre.objects.create(
            name="Comedy",
        )
        actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.movie = Movie.objects.create(
            title="Titanic",
            description="Titanic description",
            duration=123,
        )
        self.movie.genres.add(drama)
        self.movie.genres.add(comedy)
        self.movie.actors.add(actress)
        self.cinema_hall = CinemaHall.objects.create(
            name="White",
            rows=10,
            seats_in_row=14,
        )

        self.show_time_naive = datetime.datetime(
            year=2022,
            month=9,
            day=2,
            hour=9
        )

        self.movie_session = MovieSession.objects.create(
            movie=self.movie,
            cinema_hall=self.cinema_hall,
            show_time=self.show_time_naive
        )

    def test_get_movie_sessions(self):
        response = self.client.get("/api/cinema/movie_sessions/")
        movie_session_expected = {
            "movie_title": "Titanic",
            "cinema_hall_name": "White",
            "cinema_hall_capacity": 140,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        sessions_data = response.data["results"]
        self.assertEqual(len(sessions_data), 1)

        session_in_response = sessions_data[0]
        for field in movie_session_expected:
            self.assertEqual(
                session_in_response[field], movie_session_expected[field]
            )

    def test_get_movie_sessions_filtered_by_date(self):
        response = self.client.get(
            "/api/cinema/movie_sessions/?date=2022-09-02"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(
            "/api/cinema/movie_sessions/?date=2022-09-01"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_movie_sessions_filtered_by_movie(self):
        response = self.client.get(
            f"/api/cinema/movie_sessions/?movie={self.movie.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(
            "/api/cinema/movie_sessions/?movie=1234"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_movie_sessions_filtered_by_movie_and_data(self):
        url_params_1 = f"movie={self.movie.id}&date=2022-09-02"
        response = self.client.get(
            f"/api/cinema/movie_sessions/?{url_params_1}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        url_params_2 = "movie=1234&date=2022-09-02"
        response = self.client.get(
            f"/api/cinema/movie_sessions/?{url_params_2}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

        url_params_3 = f"movie={self.movie.id}&date=2022-09-03"
        response = self.client.get(
            f"/api/cinema/movie_sessions/?{url_params_3}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_post_movie_session(self):
        payload = {
            "movie": self.movie.id,
            "cinema_hall": self.cinema_hall.id,
            "show_time": datetime.datetime.now().isoformat(),
        }
        response = self.client.post(
            "/api/cinema/movie_sessions/",
            payload,
        )
        movie_sessions_db = MovieSession.objects.all()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(movie_sessions_db.count(), 2)

    def test_get_movie_session(self):
        url = f"/api/cinema/movie_sessions/{self.movie_session.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["movie"]["title"], "Titanic")
        self.assertEqual(
            response.data["movie"]["description"], "Titanic description"
        )
        self.assertEqual(response.data["movie"]["duration"], 123)
        expected_genres = sorted(["Comedy", "Drama"])
        actual_genres = sorted(response.data["movie"]["genres"])
        self.assertEqual(actual_genres, expected_genres)
        self.assertEqual(response.data["movie"]["actors"], ["Kate Winslet"])
        self.assertEqual(response.data["cinema_hall"]["capacity"], 140)
        self.assertEqual(response.data["cinema_hall"]["rows"], 10)
        self.assertEqual(response.data["cinema_hall"]["seats_in_row"], 14)
        self.assertEqual(response.data["cinema_hall"]["name"], "White")
