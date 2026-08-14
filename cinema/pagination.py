from rest_framework import pagination


class OrderPagination(pagination.PageNumberPagination):

    page_size = 1
    page_size_query_param = "page_size"
