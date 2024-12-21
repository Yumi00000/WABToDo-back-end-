import logging

from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core import permissions as custom_perm
from orders import serializers as orders_serializers
from orders.models import Order
from orders.paginations import UnacceptedOrdersPagination

logger = logging.getLogger(__name__)


class CreateOrderView(generics.CreateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = orders_serializers.CreateOrderSerializer

    def create(self, request, *args, **kwargs):
        logger.info("User %s is attempting to create an order.", request.user.username)

        try:
            response = super().create(request, *args, **kwargs)
            info_msg = "Order created successfully by user %s with name: %s"
            logger.info(info_msg, request.user.username, request.data.get("name"))
            return response

        except serializers.ValidationError as e:
            logger.warning("Validation error: %s", e.detail)
            raise

        except Exception as e:
            logger.error("Error while creating order by user %s: %s", request.user.username, str(e), exc_info=True)
            response_error_message = {"error": "An error occurred while creating the order."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditOrderView(generics.UpdateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [custom_perm.IsOrderOwnerOrAdmin]
    serializer_class = orders_serializers.UpdateOrderSerializer

    def update(self, request, *args, **kwargs):
        logger.info("User %s is attempting to update an order.", request.user.username)

        try:
            response = super().update(request, *args, **kwargs)
            info_msg = "Order with name %s updated successfully by user %s"
            logger.info(info_msg, request.data["name"], request.user.username)
            return response

        except serializers.ValidationError as e:
            logger.warning("Validation error: %s", e.detail)
            raise

        except Exception as e:
            logger.error("Error updating order by user %s: %s", request.user.username, str(e), exc_info=True)
            response_error_message = {"error": "An error occurred while updating the order"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetUnacceptedOrdersView(generics.ListAPIView, GenericViewSet):
    queryset = Order.objects.filter(accepted=False, status="pending").order_by("id")
    permission_classes = [custom_perm.IsAdminOrStaff]
    pagination_class = UnacceptedOrdersPagination
    serializer_class = orders_serializers.UnacceptedOrderSerializer

    def list(self, request, *args, **kwargs):
        logger.info("User %s is accessing unaccepted orders.", request.user.username)

        try:
            response = super().list(request, *args, **kwargs)
            info_msg = "Successfully retrieved unaccepted orders for user %s. Total orders: %d"
            logger.info(info_msg, request.user.username, len(response.data))
            return response

        except serializers.ValidationError as e:
            logger.warning("Validation error: %s", e.detail)
            raise

        except Exception as e:
            logger.error(
                "Error retrieving unaccepted orders for user %s: %s", request.user.username, str(e), exc_info=True
            )
            response_error_message = {"error": "An error occurred while retrieving orders."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderManagementView(generics.UpdateAPIView, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [custom_perm.IsAdminOrStaff]
    serializer_class = orders_serializers.OrderManagementSerializer

    def update(self, request, *args, **kwargs):
        logger.info("User %s is attempting to update an order.", request.user.username)

        try:
            response = super().update(request, *args, **kwargs)
            logger.info("The order was updated with these details: %s", request.data)
            return response

        except serializers.ValidationError as e:
            logger.warning("Validation error: %s", e.detail)
            raise

        except Exception as e:
            logger.error("Error updating order by user %s: %s", request.user.username, str(e), exc_info=True)
            response_error_message = {"error": "An error occurred while updating the order"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
