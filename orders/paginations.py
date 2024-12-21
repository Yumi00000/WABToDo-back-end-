from rest_framework.pagination import PageNumberPagination


class UnacceptedOrdersPagination(PageNumberPagination):
    page_size = 30
