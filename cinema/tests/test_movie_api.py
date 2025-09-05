from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from cinema.models import Movie, Genre, Actor
from user.models import User

class MovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="admin")
        self.client.force_authenticate(user=self.user)
        self.drama = Genre.objects.create(name="Drama")
        self.comedy = Genre.objects.create(name="Comedy")
        self.actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.movie = Movie.objects.create(title="Titanic", description="Titanic description", duration=123)
        self.movie.genres.add(self.drama, self.comedy)
        self.movie.actors.add(self.actress)

    def test_get_movies(self):
        response = self.client.get("/api/cinema/movies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "Titanic")

    def test_get_movies_filtered_by_genres(self):
        response = self.client.get(f"/api/cinema/movies/?genres={self.comedy.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_movies_filtered_by_actors(self):
        response = self.client.get(f"/api/cinema/movies/?actors={self.actress.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_movies_filtered_by_title(self):
        response = self.client.get("/api/cinema/movies/?title=Titanic")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_movies(self):
        response = self.client.post("/api/cinema/movies/", {
            "title": "Superman",
            "description": "Superman description",
            "duration": 123,
            "genres": [self.drama.id, self.comedy.id],
            "actors": [self.actress.id],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Movie.objects.filter(title="Superman").count(), 1)

    def test_post_invalid_movies(self):
        response = self.client.post("/api/cinema/movies/", {
            "title": "Superman",
            "description": "Superman description",
            "duration": 123,
            "actors": [999],
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_movie(self):
        response = self.client.get(f"/api/cinema/movies/{self.movie.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Titanic")

    def test_get_invalid_movie(self):
        response = self.client.get("/api/cinema/movies/1000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_movie(self):
        response = self.client.put(f"/api/cinema/movies/{self.movie.id}/", {
            "title": "Watchman",
            "description": "Watchman description",
            "duration": 321,
            "genres": [self.drama.id, self.comedy.id],
            "actors": [self.actress.id],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.title, "Watchman")

    def test_delete_movie(self):
        response = self.client.delete(f"/api/cinema/movies/{self.movie.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Movie.objects.filter(id=self.movie.id).exists())

    def test_delete_invalid_movie(self):
        response = self.client.delete("/api/cinema/movies/1000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
