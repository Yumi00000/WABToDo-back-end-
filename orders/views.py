from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

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
    permission_classes = [custom_perm.IsOrderOwnerOrAdmin]
    serializer_class = orders_serializers.UpdateOrderSerializer

    def update(self, request, *args, **kwargs):
        self.log_attempt_update(request.user)

        try:
            response = super().update(request, *args, **kwargs)
            self.log_successfully_updated(request.user, request.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_updating_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while updating the order"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetOrdersListView(generics.ListAPIView, GenericViewSet, OrderLoggerMixin):
    # permission_classes = [custom_perm.IsAdminOrStaff]
    pagination_class = UnacceptedOrdersPagination
    serializer_class = orders_serializers.OrdersListSerializer

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

    def get_queryset(self):
        order_status = self.request.GET.get("status")
        is_accepted = self.request.GET.get("is_accepted")
        order_by_date = self.request.GET.get("order_by_date")

        filter_kwargs = {}
        if order_status:
            filter_kwargs["status"] = order_status
        if is_accepted:
            filter_kwargs["accepted"] = is_accepted

        order_by = order_by_date if order_by_date else "-created_at"

        queryset = Order.objects.filter(**filter_kwargs).order_by(order_by)
        return queryset


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
