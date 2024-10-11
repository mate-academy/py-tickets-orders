from rest_framework.pagination import LimitOffsetPagination


class OrderPagination(LimitOffsetPagination):
    default_limit = 2
