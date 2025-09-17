from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import Movie, Genre, Actor
from user.models import User


class MovieApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username="testuser")
        self.client.force_authenticate(user=self.user)

        self.drama_genre = Genre.objects.create(name="Drama")
        self.comedy_genre = Genre.objects.create(name="Comedy")

        self.actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.actor = Actor.objects.create(first_name="Leonardo", last_name="DiCaprio")

        self.titanic_movie = Movie.objects.create(
            title="Titanic",
            description="Titanic description",
            duration=123,
        )
        self.titanic_movie.genres.add(self.drama_genre, self.comedy_genre)
        self.titanic_movie.actors.add(self.actress)

    def test_get_movies(self) -> None:
        response = self.client.get("/api/cinema/movies/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        movie_data = response.data['results'][0]

        self.assertEqual(movie_data["title"], "Titanic")
        self.assertEqual(movie_data["description"], "Titanic description")
        self.assertEqual(movie_data["duration"], 123)
        self.assertEqual(sorted([g['name'] for g in movie_data["genres"]]), sorted(["Drama", "Comedy"]))
        self.assertEqual(sorted([a['full_name'] for a in movie_data["actors"]]), sorted(["Kate Winslet"]))

    def test_get_movies_with_genres_filtering(self) -> None:
        response = self.client.get(f"/api/cinema/movies/?genres={self.comedy_genre.id}")
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(f"/api/cinema/movies/?genres={self.comedy_genre.id},2,3")
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get("/api/cinema/movies/?genres=123213")
        self.assertEqual(len(response.data['results']), 0)

    def test_get_movies_with_actors_filtering(self) -> None:
        response = self.client.get(f"/api/cinema/movies/?actors={self.actress.id}")
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(f"/api/cinema/movies/?actors={123}")
        self.assertEqual(len(response.data['results']), 0)

    def test_get_movies_with_title_filtering(self) -> None:
        response = self.client.get(f"/api/cinema/movies/?title=ita")
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(f"/api/cinema/movies/?title=ati")
        self.assertEqual(len(response.data['results']), 0)

    def test_post_movies(self) -> None:
        payload = {
            "title": "Superman",
            "description": "Superman description",
            "duration": 123,
            "actors": [self.actress.id],
            "genres": [self.drama_genre.id, self.comedy_genre.id],
        }

        response = self.client.post("/api/cinema/movies/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Movie.objects.count(), 2)
        self.assertTrue(Movie.objects.filter(title="Superman").exists())

    def test_post_invalid_movies(self) -> None:
        response = self.client.post(
            "/api/cinema/movies/",
            {
                "title": "Superman",
                "description": "Superman description",
                "duration": 123,
                "actors": [
                    {
                        "id": 3,
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Movie.objects.filter(title="Superman").exists())

    def test_get_movie(self) -> None:
        response = self.client.get(f"/api/cinema/movies/{self.titanic_movie.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Titanic")
        self.assertEqual(response.data["description"], "Titanic description")
        self.assertEqual(response.data["duration"], 123)
        self.assertEqual(sorted([g['name'] for g in response.data["genres"]]), sorted(["Drama", "Comedy"]))
        self.assertEqual(sorted([a['full_name'] for a in response.data["actors"]]), sorted(["Kate Winslet"]))

    def test_get_invalid_movie(self) -> None:
        response = self.client.get("/api/cinema/movies/1000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_movie(self) -> None:
        payload = {
            "title": "Watchman",
            "description": "Watchman description",
            "duration": 321,
            "genres": [self.drama_genre.id],
            "actors": [self.actor.id],
        }
        response = self.client.put(f"/api/cinema/movies/{self.titanic_movie.id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.titanic_movie.refresh_from_db()
        self.assertEqual(self.titanic_movie.title, "Watchman")
        self.assertEqual(self.titanic_movie.description, "Watchman description")
        self.assertEqual(self.titanic_movie.duration, 321)
        self.assertEqual(self.titanic_movie.genres.count(), 1)
        self.assertTrue(self.titanic_movie.genres.filter(id=self.drama_genre.id).exists())
        self.assertEqual(self.titanic_movie.actors.count(), 1)
        self.assertTrue(self.titanic_movie.actors.filter(id=self.actor.id).exists())

    def test_delete_movie(self) -> None:
        response = self.client.delete(f"/api/cinema/movies/{self.titanic_movie.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Movie.objects.filter(id=self.titanic_movie.id).exists())
        self.assertEqual(Movie.objects.count(), 0)

    def test_delete_invalid_movie(self) -> None:
        response = self.client.delete("/api/cinema/movies/1000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
