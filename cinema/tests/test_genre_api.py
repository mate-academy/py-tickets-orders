from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from cinema.models import Genre


class GenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Genre.objects.create(name="Comedy")
        Genre.objects.create(name="Drama")

    def test_get_genres(self):
        response = self.client.get("/api/cinema/genres/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Исправлено: берем данные из ["results"]
        genres = [genre["name"] for genre in response.data["results"]]

        self.assertEqual(sorted(genres), ["Comedy", "Drama"])

    def test_post_genres(self):
        response = self.client.post(
            "/api/cinema/genres/",
            {"name": "Sci-fi"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Genre.objects.count(), 3)
        self.assertTrue(Genre.objects.filter(name="Sci-fi").exists())

    def test_get_invalid_genre(self):
        response = self.client.get("/api/cinema/genres/1001/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_genre(self):
        genre = Genre.objects.first()
        response = self.client.delete(f"/api/cinema/genres/{genre.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Genre.objects.filter(id=genre.id).exists())
