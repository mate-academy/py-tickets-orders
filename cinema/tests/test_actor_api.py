from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from cinema.models import Actor


class ActorApiTests(TestCase):
    from django.test import TestCase
    from rest_framework import status
    from rest_framework.test import APIClient
    from cinema.models import Actor

    class ActorApiTests(TestCase):
        def setUp(self):
            self.client = APIClient()
            Actor.objects.create(first_name="George", last_name="Clooney")
            Actor.objects.create(first_name="Keanu", last_name="Reeves")

        def test_get_actors(self):
            response = self.client.get("/api/cinema/actors/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            actors_full_names = [actor["full_name"] for actor in response.data["results"]]
            self.assertEqual(
                sorted(actors_full_names), ["George Clooney", "Keanu Reeves"]
            )

        def test_post_actors(self):
            response = self.client.post(
                "/api/cinema/actors/",
                {"first_name": "Scarlett", "last_name": "Johansson"},
            )
            db_actors = Actor.objects.all()
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(db_actors.count(), 3)
            self.assertEqual(db_actors.filter(first_name="Scarlett").count(), 1)

        def test_get_invalid_actor(self):
            response = self.client.get("/api/cinema/actors/1001/")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        def test_put_actor(self):
            actor = Actor.objects.first()
            response = self.client.put(
                f"/api/cinema/actors/{actor.id}/",
                {"first_name": "Scarlett", "last_name": "Johansson"},
            )
            actor.refresh_from_db()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(actor.first_name, "Scarlett")
            self.assertEqual(actor.last_name, "Johansson")

        def test_delete_actor(self):
            actor = Actor.objects.first()
            response = self.client.delete(f"/api/cinema/actors/{actor.id}/")
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(Actor.objects.filter(id=actor.id).exists())
