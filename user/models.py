from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.IntegerField(primary_key=True)
