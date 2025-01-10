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
    """
    Handles the creation of orders through API while incorporating logging functionality for
    various events such as creation attempts, successes, validation errors, and general errors.

    This class extends `generics.CreateAPIView` and `GenericViewSet` to provide standard
    Create API behavior and integrates custom logging logic from `OrderLoggerMixin`. It defines
    customized behavior for order creation, ensuring detailed logging for operational insights.

    Attributes:
        queryset: The queryset representing the collection of all `Order` objects.
        permission_classes: The list of permission classes enforcing `IsAuthenticated` to ensure
            only authenticated users can create orders.
        serializer_class: The serializer class `CreateOrderSerializer` which validates data for
            creating orders and controls serialization/deserialization of input/output data.
    """
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
    """
    Allows users to update an order with proper logging for update attempts and errors.

    This class serves as a combination view for handling order updates securely. It
    validates user permissions, updates the order information based on the provided
    serializer, and logs attempts, errors, and successful updates for diagnostic
    and audit purposes. It supports custom permissions to ensure only the order owner
    or an admin can perform updates.

    Attributes:
        queryset: Order
            Queryset that provides all Order objects for the view.
        permission_classes: list
            List of permission classes used to determine if the user has sufficient
            permission to update the order. Includes custom and built-in permissions.
        serializer_class: Type[serializers.Serializer]
            Serializer class used to validate and process order update data.
    """
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


class GetOrdersListView(generics.ListAPIView, GenericViewSet, OrderLoggerMixin):
    """
    Provides a view for retrieving a list of orders with flexible filtering and ordering.

    This class-based view leverages Django's generics.ListAPIView and provides a highly
    customizable way to retrieve order data. It allows filtering by order status and
    acceptance status and supports sorting orders by creation date. Additionally, the
    view logs various aspects of the request and response process, including unaccepted
    orders, retrieved orders, and any errors encountered during the operation.

    Attributes:
        permission_classes: A list of permissions, restricting access to the view based
            on user roles. This view allows access only to admin or staff users.
        pagination_class: Specifies the pagination class to handle order responses. In
            this view, unaccepted orders are paginated.
        serializer_class: Indicates the serializer class used for formatting the output
            of the orders list.
    """
    permission_classes = [custom_perm.IsAdminOrStaff]
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
    """
    Manages update operations for orders.

    This class allows authorized users (admin or staff) to update order details through API
    requests. It includes logging mechanisms to track updates, validation errors, and
    unexpected errors during the update process.

    Attributes:
        queryset: Queryset containing all order objects to be managed.
        permission_classes: List of permission classes that define access control.
        serializer_class: Serializer used for validating and deserializing input data
            for order updates.
    """
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
