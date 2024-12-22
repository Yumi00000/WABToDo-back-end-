import logging

from django.contrib.auth import get_user_model

User = get_user_model()


class OrderLoggerMixin:
    _logger = logging.getLogger(__name__)
    _log_messages = {
        # Success
        # Base user actions:
        "attempt_create": "User %s is attempting to create an order.",
        "attempt_update": "User %s is attempting to update an order.",
        "order_created": "Order created successfully by user %s with name: %s",
        "order_updated": "Order with name %s updated successfully by user %s",
        # Admin user actions:
        "user_get_unaccepted_orders": "User %s is accessing unaccepted orders.",
        "retrieved": "Successfully retrieved unaccepted orders for user %s. Total orders: %d",
        "admin_update": "The order was updated with these details: %s",
        # Warning
        "is_invalid": "Validation error: %s",
        # Error
        "creation_error": "Error while creating order by user %s: %s",
        "updating_error": "Error updating order by user %s: %s",
        "retrieve_error": "Error retrieving unaccepted orders for user %s: %s",
    }

    # Logs for base user
    def log_attempt_create(self, user: User) -> None:
        self._logger.info(self._log_messages["attempt_create"], user.username)

    def log_attempt_update(self, user: User) -> None:
        self._logger.info(self._log_messages["attempt_update"], user.username)

    def log_successfully_created(self, user, request_data):
        self._logger.info(self._log_messages["order_created"], user.username, request_data["name"])

    def log_successfully_updated(self, user: User, request_data: dict) -> None:
        self._logger.info(self._log_messages["order_updated"], request_data["name"], user.username)

    # Logs for admin user
    def log_unaccepted_orders(self, user: User) -> None:
        self._logger.info(self._log_messages["user_get_unaccepted_orders"], user)

    def log_retrieved_orders(self, user: User, response_data: dict) -> None:
        self._logger.info(self._log_messages["retrieved"], user.username, len(response_data))

    def log_admin_update(self, request_data: dict) -> None:
        self._logger.info(self._log_messages["admin_update"], request_data[""])

    # Warn logs -> ValidationError
    def log_validation_error(self, error_detail: str) -> None:
        self._logger.warning(self._log_messages["is_invalid"], error_detail)

    # Error logs
    def log_creation_error(self, user: User, error: str) -> None:
        self._logger.error(self._log_messages["creation_error"], user.username, error, exc_info=True)

    def log_updating_error(self, user: User, error: str) -> None:
        self._logger.error(self._log_messages["updating_error"], user.username, error, exc_info=True)

    def log_retrieving_error(self, user: User, error: str) -> None:
        self._logger.error(self._log_messages["retrieve_error"], user.username, error, exc_info=True)
