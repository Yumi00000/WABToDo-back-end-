from rest_framework import generics, permissions
from rest_framework.viewsets import GenericViewSet

from core import permissions as custom_perm
from orders import serializers
from orders.models import Order


class CreateOrderView(generics.CreateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CreateOrderSerializer


class EditOrderView(generics.UpdateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [custom_perm.IsOrderOwnerOrAdmin]
    serializer_class = serializers.UpdateOrderSerializer


class GetUnacceptedOrdersView(generics.ListAPIView, GenericViewSet):
    queryset = Order.objects.filter(accepted=False, status="active")
    permission_classes = [custom_perm.IsAdminOrStaff]
    serializer_class = serializers.UnacceptedOrderSerializer


class OrderManagementView(generics.UpdateAPIView, GenericViewSet):
    queryset = Order.objects.filter(status="active")
    permission_classes = [custom_perm.IsAdminOrStaff]
    serializer_class = serializers.AcceptOrderSerializer
