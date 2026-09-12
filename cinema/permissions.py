from rest_framework.permissions import IsAuthenticatedOrReadOnly


class IsAdminOrIfAuthenticatedReadOnly(IsAuthenticatedOrReadOnly):
    def has_permission(self, request, view):
        return bool(
            request.method in self.SAFE_METHODS
            and request.user
            and request.user.is_authenticated
            or request.user
            and request.user.is_staff
        )
