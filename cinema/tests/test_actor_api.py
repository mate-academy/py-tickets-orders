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
        self.assertIn("results", response.data)
        actors_data_list = response.data["results"]
        actors_full_names = [actor["full_name"] for actor in actors_data_list]
        self.assertEqual(
            sorted(actors_full_names), ["George Clooney", "Keanu Reeves"]
        )

    def test_post_actors(self):
        response = self.client.post(
            "/api/cinema/actors/",
            {
                "first_name": "Scarlett",
                "last_name": "Johansson",
            },
        )
        db_actors = Actor.objects.all()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_actors.count(), 3)
        self.assertEqual(db_actors.filter(first_name="Scarlett").count(), 1)
        created_actor_data = response.data
        self.assertEqual(created_actor_data["first_name"], "Scarlett")
        self.assertEqual(created_actor_data["last_name"], "Johansson")

    def test_get_invalid_actor(self):
        response = self.client.get("/api/cinema/actors/1001/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_actor(self):
        actor_to_update = Actor.objects.order_by("id").first()
        self.assertIsNotNone(actor_to_update, "No actor found to update")

        response = self.client.put(
            f"/api/cinema/actors/{actor_to_update.id}/",
            {
                "first_name": "Scarlett",
                "last_name": "Johansson",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        actor_pk_1 = Actor.objects.get(
            pk=actor_to_update.id)
        self.assertEqual(
            [
                actor_pk_1.first_name,
                actor_pk_1.last_name,
            ],
            [
                "Scarlett",
                "Johansson",
            ],
        )

    def test_delete_actor(self):
        actor_to_delete = Actor.objects.order_by("id").first()
        self.assertIsNotNone(actor_to_delete, "No actor found to delete")

        response = self.client.delete(
            f"/api/cinema/actors/{actor_to_delete.id}/",
        )
        db_actors_id_1 = Actor.objects.filter(id=1)
        self.assertEqual(db_actors_id_1.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_invalid_actor(self):
        response = self.client.delete(
            "/api/cinema/actors/1000/",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
