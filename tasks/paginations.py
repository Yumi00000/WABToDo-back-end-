from rest_framework.pagination import PageNumberPagination


class TasksPagination(PageNumberPagination):
    page_size = 20
