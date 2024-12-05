from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as custom_perm
from orders.models import Order
from orders import serializers


class CreateOrderView(generics.CreateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CreateOrderSerializer


class EditOrderView(generics.UpdateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [custom_perm.IsOrderOwnerOrAdmin]
    serializer_class = serializers.UpdateOrderSerializer
