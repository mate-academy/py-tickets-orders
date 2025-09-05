import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from cinema.models import Movie, Genre, Actor, CinemaHall, MovieSession
from user.models import User

class MovieSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="admin")
        self.client.force_authenticate(user=self.user)
        drama = Genre.objects.create(name="Drama")
        comedy = Genre.objects.create(name="Comedy")
        actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.movie = Movie.objects.create(title="Titanic", description="Titanic description", duration=123)
        self.movie.genres.add(drama, comedy)
        self.movie.actors.add(actress)
        self.cinema_hall = CinemaHall.objects.create(name="White", rows=10, seats_in_row=14)
        self.movie_session = MovieSession.objects.create(
            movie=self.movie,
            cinema_hall=self.cinema_hall,
            show_time=datetime.datetime(2022, 9, 2, 9)
        )

    def test_get_movie_sessions(self):
        response = self.client.get("/api/cinema/movie_sessions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["movie_title"], "Titanic")

    def test_get_movie_sessions_filtered_by_date(self):
        response = self.client.get("/api/cinema/movie_sessions/?date=2022-09-02")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_movie_sessions_filtered_by_movie(self):
        response = self.client.get(f"/api/cinema/movie_sessions/?movie={self.movie.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_movie_sessions_filtered_by_movie_and_date(self):
        response = self.client.get(f"/api/cinema/movie_sessions/?movie={self.movie.id}&date=2022-09-02")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_movie_session(self):
        response = self.client.post("/api/cinema/movie_sessions/", {
            "movie": self.movie.id,
            "cinema_hall": self.cinema_hall.id,
            "show_time": datetime.datetime.now()
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_movie_session(self):
        response = self.client.get(f"/api/cinema/movie_sessions/{self.movie_session.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["movie"]["title"], "Titanic")
