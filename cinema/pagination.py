from rest_framework.pagination import PageNumberPagination


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "per_page"
    max_page_size = 10
