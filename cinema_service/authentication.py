from django.contrib.auth import get_user_model
from rest_framework import authentication


class AlwaysAuth(authentication.BaseAuthentication):
    def authenticate(self, request):
        user, _ = get_user_model().objects.get_or_create(username="admin.user")
        return (user, None)
