from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from orders.models import Order
from orders import serializers


class CreateOrderView(generics.CreateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CreateOrderSerializer
