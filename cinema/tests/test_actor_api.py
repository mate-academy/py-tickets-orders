from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import Actor
from user.models import User


class ActorApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.actor = Actor.objects.create(first_name="Leonardo", last_name="DiCaprio")
        self.user = User.objects.create(username="admin")
        self.client.force_authenticate(user=self.user)

    def test_get_actors(self) -> None:
        response = self.client.get("/api/cinema/actors/")

        actors_full_names = [f"{actor['first_name']} {actor['last_name']}" for actor in response.data["results"]]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Leonardo DiCaprio", actors_full_names)

    def test_create_actor(self) -> None:
        payload = {"first_name": "Kate", "last_name": "Winslet"}
        response = self.client.post("/api/cinema/actors/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        actor = Actor.objects.get(id=response.data["id"])
        for key, value in payload.items():
            self.assertEqual(getattr(actor, key), value)

    def test_put_actor(self) -> None:
        payload = {"first_name": "Brad", "last_name": "Pitt"}
        response = self.client.put(f"/api/cinema/actors/{self.actor.id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.actor.refresh_from_db()
        self.assertEqual(self.actor.first_name, "Brad")
        self.assertEqual(self.actor.last_name, "Pitt")

    def test_delete_actor(self) -> None:
        response = self.client.delete(f"/api/cinema/actors/{self.actor.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Actor.objects.filter(id=self.actor.id).exists())
