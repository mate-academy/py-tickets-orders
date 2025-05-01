import datetime
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from cinema.models import Movie, Genre, Actor, MovieSession, CinemaHall, Ticket

MOVIE_SESSION_URL = "/api/cinema/movie_sessions/"


class MovieSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.genre = Genre.objects.create(name="Drama")
        self.genre2 = Genre.objects.create(name="Comedy")
        self.actor = Actor.objects.create(
            first_name="Kate",
            last_name="Winslet"
        )
        self.movie = Movie.objects.create(
            title="Titanic",
            description="Titanic description",
            duration=123,
        )
        self.movie.genres.add(self.genre, self.genre2)
        self.movie.actors.add(self.actor)

        self.cinema_hall = CinemaHall.objects.create(
            name="White",
            rows=10,
            seats_in_row=14
        )

        self.movie_session = MovieSession.objects.create(
            show_time="2022-09-02 09:00:00",
            movie=self.movie,
            cinema_hall=self.cinema_hall
        )

    def test_get_movie_sessions(self):
        movie_sessions = self.client.get("/api/cinema/movie_sessions/")
        movie_session = {
            "movie_title": "Titanic",
            "cinema_hall_name": "White",
            "cinema_hall_capacity": 140,
        }
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        for field in movie_session:
            self.assertEqual(
                movie_sessions.data[0][field], movie_session[field]
            )

    def test_get_movie_sessions_filtered_by_date(self):
        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?date=2022-09-02"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data), 1)

        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?date=2022-09-01"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data), 0)

    def test_get_movie_sessions_filtered_by_movie(self):
        movie_sessions = self.client.get(
            f"/api/cinema/movie_sessions/?movie={self.movie.id}"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data), 1)

        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?movie=1234"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data), 0)

    def test_get_movie_sessions_filtered_by_movie_and_data(self):
        movie_sessions = self.client.get(
            f"/api/cinema/movie_sessions/?movie={self.movie.id}&date=2022-09-2"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data), 1)

        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?movie=1234&date=2022-09-2"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data), 0)

        movie_sessions = self.client.get(
            f"/api/cinema/movie_sessions/?movie={self.movie.id}&date=2022-09-3"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data), 0)

    def test_post_movie_session(self):
        movies = self.client.post(
            "/api/cinema/movie_sessions/",
            {
                "movie": 1,
                "cinema_hall": 1,
                "show_time": datetime.datetime.now(),
            },
        )
        movie_sessions = MovieSession.objects.all()
        self.assertEqual(movies.status_code, status.HTTP_201_CREATED)
        self.assertEqual(movie_sessions.count(), 2)

    def test_get_movie_session(self):
        response = self.client.get(f"{MOVIE_SESSION_URL}{self.movie_session.id}/")

        self.assertEqual(response.data["show_time"], "2022-09-02T09:00:00")
        self.assertEqual(response.data["movie"]["title"], "Titanic")
        self.assertEqual(response.data["movie"]["description"], "Titanic description")
        self.assertEqual(response.data["movie"]["duration"], 123)
        self.assertEqual(
            sorted(response.data["movie"]["genres"]),
            ["Comedy", "Drama"]
        )
        self.assertEqual(
            sorted(response.data["movie"]["actors"]),
            ["Kate Winslet"]
        )
        self.assertEqual(response.data["cinema_hall"]["name"], "White")
        self.assertEqual(response.data["cinema_hall"]["rows"], 10)
        self.assertEqual(response.data["cinema_hall"]["seats_in_row"], 14)
        self.assertEqual(response.data["cinema_hall"]["capacity"], 140)
        self.assertEqual(response.data["taken_places"], [])
