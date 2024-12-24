from rest_framework.pagination import PageNumberPagination


class DashboardPagination(PageNumberPagination):
    page_size = 5
