from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from cinema.models import MovieSession


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    created = models.DateTimeField(auto_now_add=True)


class User(AbstractUser):
    pass
