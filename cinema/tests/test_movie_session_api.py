import datetime

from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import Movie, Genre, Actor, MovieSession, CinemaHall
from user.models import User


class MovieSessionApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username="testuser")
        self.client.force_authenticate(user=self.user)

        self.drama = Genre.objects.create(name="Drama")
        self.comedy = Genre.objects.create(name="Comedy")
        self.actress = Actor.objects.create(first_name="Kate", last_name="Winslet")

        self.movie = Movie.objects.create(
            title="Titanic",
            description="Titanic description",
            duration=123,
        )
        self.movie.genres.add(self.drama, self.comedy)
        self.movie.actors.add(self.actress)

        self.cinema_hall = CinemaHall.objects.create(
            name="White",
            rows=10,
            seats_in_row=14,
        )
        self.movie_session = MovieSession.objects.create(
            movie=self.movie,
            cinema_hall=self.cinema_hall,
            show_time=datetime.datetime(
                year=2022,
                month=9,
                day=2,
                hour=9
            ),
        )

    def test_get_movie_sessions(self) -> None:
        response = self.client.get("/api/cinema/movie_sessions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        movie_session_data = response.data["results"][0]
        self.assertEqual(movie_session_data["movie_title"], "Titanic")
        self.assertEqual(movie_session_data["cinema_hall_name"], "White")
        self.assertEqual(movie_session_data["cinema_hall_capacity"], 140)

    def test_get_movie_sessions_filtered_by_date(self) -> None:
        response = self.client.get("/api/cinema/movie_sessions/?date=2022-09-02")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get("/api/cinema/movie_sessions/?date=2022-09-01")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_movie_sessions_filtered_by_movie(self) -> None:
        response = self.client.get(f"/api/cinema/movie_sessions/?movie={self.movie.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get("/api/cinema/movie_sessions/?movie=1234")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_movie_sessions_filtered_by_movie_and_data(self) -> None:
        response = self.client.get(f"/api/cinema/movie_sessions/?movie={self.movie.id}&date=2022-09-02")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get("/api/cinema/movie_sessions/?movie=1234&date=2022-09-02")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

        response = self.client.get(f"/api/cinema/movie_sessions/?movie={self.movie.id}&date=2022-09-03")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_post_movie_session(self) -> None:
        initial_count = MovieSession.objects.count()
        payload = {
            "movie": self.movie.id,
            "cinema_hall": self.cinema_hall.id,
            "show_time": "2022-09-03T10:00:00Z",
        }

        response = self.client.post("/api/cinema/movie_sessions/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MovieSession.objects.count(), initial_count + 1)

        new_session = MovieSession.objects.get(id=response.data["id"])
        self.assertEqual(new_session.movie.id, self.movie.id)
        self.assertEqual(new_session.cinema_hall.id, self.cinema_hall.id)

    def test_get_movie_session(self) -> None:
        response = self.client.get(f"/api/cinema/movie_sessions/{self.movie_session.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["movie"]["title"], "Titanic")
        self.assertEqual(response.data["movie"]["description"], "Titanic description")
        self.assertEqual(response.data["movie"]["duration"], 123)
        self.assertEqual(sorted([g["name"] for g in response.data["movie"]["genres"]]), sorted(["Drama", "Comedy"]))
        self.assertEqual(sorted([a["full_name"] for a in response.data["movie"]["actors"]]), sorted(["Kate Winslet"]))
        self.assertEqual(response.data["cinema_hall"]["capacity"], 140)
        self.assertEqual(response.data["cinema_hall"]["rows"], 10)
        self.assertEqual(response.data["cinema_hall"]["seats_in_row"], 14)
        self.assertEqual(response.data["cinema_hall"]["name"], "White")

    def test_put_movie_session(self) -> None:
        new_movie = Movie.objects.create(title="Avatar", description="Avatar description", duration=180)

        payload = {
            "movie": new_movie.id,
            "cinema_hall": self.cinema_hall.id,
            "show_time": "2023-10-01T15:00:00Z",
        }
        response = self.client.put(f"/api/cinema/movie_sessions/{self.movie_session.id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.movie_session.refresh_from_db()
        self.assertEqual(self.movie_session.movie.id, new_movie.id)
        self.assertEqual(self.movie_session.show_time,
                         datetime.datetime(2023, 10, 1, 15, 0, tzinfo=datetime.timezone.utc))

    def test_delete_movie_session(self) -> None:
        initial_count = MovieSession.objects.count()
        response = self.client.delete(f"/api/cinema/movie_sessions/{self.movie_session.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MovieSession.objects.filter(id=self.movie_session.id).exists())
        self.assertEqual(MovieSession.objects.count(), initial_count - 1)

    def test_delete_invalid_movie_session(self) -> None:
        response = self.client.delete("/api/cinema/movie_sessions/1000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
