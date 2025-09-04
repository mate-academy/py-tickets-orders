from rest_framework import pagination


class OrderPagination(pagination.PageNumberPagination):
    page_size = 2
