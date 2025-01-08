from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django.http import response as dj_res

from core import permissions as custom_perm
from orders import serializers as orders_serializers
from orders.mixins import OrderLoggerMixin
from orders.models import Order
from orders.paginations import UnacceptedOrdersPagination


class CreateOrderView(generics.CreateAPIView, GenericViewSet, OrderLoggerMixin):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = orders_serializers.CreateOrderSerializer

    def create(self, request, *args, **kwargs):
        self.log_attempt_create(request.user)

        try:
            response = super().create(request, *args, **kwargs)
            self.log_successfully_created(request.user, request.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_creation_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while creating the order."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditOrderView(generics.UpdateAPIView, GenericViewSet, OrderLoggerMixin):
    queryset = Order.objects.all()
    permission_classes = [custom_perm.IsOrderOwnerOrAdmin, permissions.IsAuthenticated]
    serializer_class = orders_serializers.UpdateOrderSerializer

    def update(self, request, *args, **kwargs):
        self.log_attempt_update(request.user)

        try:
            response = super().update(request, *args, **kwargs)
            self.log_successfully_updated(request.user, response.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except dj_res.Http404:
            self.log_validation_error("Order not found")
            raise

        except Exception as e:
            self.log_updating_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while updating the order"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetUnacceptedOrdersView(generics.ListAPIView, GenericViewSet, OrderLoggerMixin):
    queryset = Order.objects.filter(accepted=False, status="pending").order_by("id")
    permission_classes = [custom_perm.IsAdminOrStaff]
    pagination_class = UnacceptedOrdersPagination
    serializer_class = orders_serializers.UnacceptedOrderSerializer

    def list(self, request, *args, **kwargs):
        self.log_unaccepted_orders(request.user)

        try:
            response = super().list(request, *args, **kwargs)
            self.log_retrieved_orders(request.user, response.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_retrieving_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while retrieving orders."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderManagementView(generics.UpdateAPIView, GenericViewSet, OrderLoggerMixin):
    queryset = Order.objects.all()
    permission_classes = [custom_perm.IsAdminOrStaff]
    serializer_class = orders_serializers.OrderManagementSerializer

    def update(self, request, *args, **kwargs):
        self.log_attempt_update(request.user)

        try:
            response = super().update(request, *args, **kwargs)
            self.log_admin_update(request.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_updating_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while updating the order"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
