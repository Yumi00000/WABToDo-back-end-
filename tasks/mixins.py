import logging

from django.contrib.auth import get_user_model

User = get_user_model()


class TaskLoggerMixin:
    """
    Provides logging functionalities specific to task operations.

    This mixin class is designed to provide logging support for actions related to task
    management, such as retrieving, creating, updating, and deleting tasks. It captures
    logging for both successful operations and error cases, ensuring that both user activity
    and potential issues can be tracked effectively. The class structure and logging provide
    methods that can be integrated into applications requiring detailed audit logs for task
    manipulations.

    Attributes:
        _logger (Logger): Logger instance used for logging events.
        _log_messages (dict): A dictionary containing predefined log message templates.
            Keys represent event categories like attempts, successes, warnings, and errors.
            Values are formatted string templates used in log messages.

    Methods:
        log_attempt_retrieve_tasks(user: User)
            Logs an informational message when a user attempts to retrieve tasks.

        log_attempt_create(user: User)
            Logs an informational message when a user attempts to create a task.

        log_attempt_update(user: User)
            Logs an informational message when a user attempts to update a task.

        log_attempt_delete(user: User)
            Logs an informational message when a user attempts to delete a task.

        log_successfully_retrieve(user: User, response_data: dict)
            Logs an informational message when a user successfully retrieves tasks.

        log_successfully_created(user: User, request_data: dict)
            Logs an informational message when a user successfully creates a task.

        log_successfully_updated(user: User, request_data: dict)
            Logs an informational message when a user successfully updates a task.

        log_successfully_deleted(user: User)
            Logs an informational message when a user successfully deletes a task.

        log_validation_error(error_detail: str)
            Logs a warning message when a validation error is encountered.

        log_retrieve_error(user: User, error: str)
            Logs an error message when there is a problem retrieving tasks.

        log_creation_error(user: User, error: str)
            Logs an error message when there is a problem creating a task.

        log_updating_error(user: User, error: str)
            Logs an error message when there is a problem updating a task.

        log_deleting_error(user: User, error: str)
            Logs an error message when there is a problem deleting a task.
    """
    _logger = logging.getLogger(__name__)
    _log_messages = {
        # Attempts
        "attempt_retrieve_tasks": "User %s is attempting to retrieve list of tasks.",
        "attempt_create": "User %s is attempting to create an task.",
        "attempt_update": "User %s is attempting to update an task.",
        "attempt_delete": "User %s is attempting to delete an task.",
        # Success
        "success_retrieve_tasks": "User %s is accessing list of tasks. Total tasks: %s",
        "success_creation_task": "Task created successfully by user %s with title: %s",
        "success_updating_task": "Task with title %s updated successfully by user %s",
        "success_deleting_task": "Task was deleted successfully by user %s",
        # Warning
        "is_invalid": "Validation error: %s",
        # Error
        "error_retrieve_tasks": "Error retrieving list of tasks for user %s: %s",
        "creation_error": "Error while creating task by user %s: %s",
        "updating_error": "Error updating task by user %s: %s",
        "deleting_error": "Error deleting task by user %s: %s",
    }

    # Attempts
    def log_attempt_retrieve_tasks(self, user: User):
        self._logger.info(self._log_messages["attempt_retrieve_tasks"], user.username)

    def log_attempt_create(self, user: User) -> None:
        self._logger.info(self._log_messages["attempt_create"], user.username)

    def log_attempt_update(self, user: User) -> None:
        self._logger.info(self._log_messages["attempt_update"], user.username)

    def log_attempt_delete(self, user: User) -> None:
        self._logger.info(self._log_messages["attempt_delete"], user.username)

    # Success
    def log_successfully_retrieve(self, user: User, response_data: dict) -> None:
        self._logger.info(self._log_messages["success_retrieve_tasks"], user.username, len(response_data))

    def log_successfully_created(self, user: User, request_data: dict) -> None:
        self._logger.info(self._log_messages["success_creation_task"], user.username, request_data["title"])

    def log_successfully_updated(self, user: User, request_data: dict) -> None:
        self._logger.info(self._log_messages["success_updating_task"], request_data["title"], user.username)

    def log_successfully_deleted(self, user: User) -> None:
        self._logger.info(self._log_messages["success_deleting_task"], user.username)

    # Warn logs -> ValidationError
    def log_validation_error(self, error_detail: str) -> None:
        self._logger.warning(self._log_messages["is_invalid"], error_detail)

    # Errors
    def log_retrieve_error(self, user: User, error: str) -> None:
        self._logger.warning(self._log_messages["error_retrieve_tasks"], user.username, error, exc_info=True)

    def log_creation_error(self, user: User, error: str) -> None:
        self._logger.error(self._log_messages["creation_error"], user.username, error, exc_info=True)

    def log_updating_error(self, user: User, error: str) -> None:
        self._logger.error(self._log_messages["updating_error"], user.username, error, exc_info=True)

    def log_deleting_error(self, user: User, error: str) -> None:
        self._logger.error(self._log_messages["deleting_error"], user.username, error, exc_info=True)
