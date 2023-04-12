from rest_framework.pagination import PageNumberPagination


class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 50


def query_params_str_to_int(queryset):
    return [int(id_) for id_ in queryset.split(",")]
