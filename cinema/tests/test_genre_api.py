from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from cinema.models import Genre
from user.models import User

class GenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="admin")
        self.client.force_authenticate(user=self.user)
        Genre.objects.create(name="Comedy")
        Genre.objects.create(name="Drama")

    def test_get_genres(self):
        response = self.client.get("/api/cinema/genres/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        genres = [g["name"] for g in response.data]
        self.assertEqual(sorted(genres), ["Comedy", "Drama"])

    def test_post_genres(self):
        response = self.client.post("/api/cinema/genres/", {"name": "Sci-fi"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Genre.objects.filter(name="Sci-fi").count(), 1)

    def test_get_invalid_genre(self):
        response = self.client.get("/api/cinema/genres/1001/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_genre(self):
        response = self.client.put("/api/cinema/genres/1/", {"name": "Sci-fi"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_genre(self):
        response = self.client.delete("/api/cinema/genres/1/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Genre.objects.filter(id=1).count(), 0)

    def test_delete_invalid_genre(self):
        response = self.client.delete("/api/cinema/genres/1000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
