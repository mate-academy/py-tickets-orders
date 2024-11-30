from rest_framework.pagination import PageNumberPagination


class OrderSetPagination(PageNumberPagination):
    page_size = 1
