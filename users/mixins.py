import logging


class UserLoggerMixin:
    _logger = logging.getLogger(__name__)
    _log_messages = {
        # Attempts
        "attempt_retrieve_dashboard": "The user is attempting to retrieve information on the dashboard",
        # Success
        "success_retrieve_dashboard": "Dashboard information has been successfully retrieved by the user",
        # Warning
        "is_invalid": "Validation error %s",
        # Error
        "error_retrieve_dashboard": "Error while retrieving dashboard information, details: %s",
    }

    # Attempts
    def log_attempt_retrieve_dashboard(self) -> None:
        self._logger.info(self._log_messages["attempt_retrieve_dashboard"])

    # Success
    def log_successfully_retrieved_dashboard(self) -> None:
        self._logger.info(self._log_messages["success_retrieve_dashboard"])

    # Warning -> ValidationError
    def log_validation_error(self, error_detail: str) -> None:
        self._logger.warning(self._log_messages["is_invalid"], error_detail)

    # Errors
    def log_error_retrieving(self, error: str) -> None:
        self._logger.error(self._log_messages["error_retrieve_dashboard"], error)


class TeamLoggerMixin:
    _logger = logging.getLogger(__name__)
    _log_messages = {
        # Attempts
        "attempt_team_list": "The user is attempting to retrieve a list of available teams",
        "attempt_team_details": "The user is attempting to retrieve team details",
        "attempt_team_create": "The user is attempting to create a new team",
        "attempt_team_update": "The user is attempting to update an existing team",
        # Success
        "success_retrieve_team_list": "The list of teams was successfully retrieved",
        "success_retrieve_team_details": "Details about the team have been successfully retrieved",
        "success_created_team": "The new team has been successfully created",
        "success_updated_team": "The team has been successfully updated",
        # Warning
        "is_invalid": "Validation error %s",
        # Error
        "error_retrieve": "Error while retrieving list of teams, details: %s",
        "error_retrieve_team_details": "Error while retrieving team details, error details: %s",
        "error_creation_team": "Error while creating the team, details: %s",
        "error_updating_team": "Error while updating the team, details: %s",
    }

    # Attempts
    def log_attempt_retrieve_list_of_teams(self) -> None:
        self._logger.info(self._log_messages["attempt_team_list"])

    def log_attempt_retrieve_team_details(self) -> None:
        self._logger.info(self._log_messages["attempt_team_details"])

    def log_attempt_create_team(self) -> None:
        self._logger.info(self._log_messages["attempt_team_create"])

    def log_attempt_update_team(self) -> None:
        self._logger.info(self._log_messages["attempt_team_update"])

    # Success
    def log_successfully_retrieved_list_of_teams(self) -> None:
        self._logger.info(self._log_messages["success_retrieve_team_list"])

    def log_successful_retrieve_team_details(self) -> None:
        self._logger.info(self._log_messages["success_retrieve_team_details"])

    def log_successfully_created(self) -> None:
        self._logger.info(self._log_messages["success_created_team"])

    def log_successfully_updated(self) -> None:
        self._logger.info(self._log_messages["success_updated_team"])

    # Warning -> ValidationError
    def log_validation_error(self, error_detail: str) -> None:
        self._logger.warning(self._log_messages["is_invalid"], error_detail)

    # Errors
    def log_error_retrieving(self, error: str) -> None:
        self._logger.error(self._log_messages["error_retrieve"], error, exc_info=True)

    def logg_error_retrieving_details(self, error: str) -> None:
        self._logger.error(self._log_messages["error_retrieve_team_details"], error, exc_info=True)

    def log_error_creating(self, error: str) -> None:
        self._logger.error(self._log_messages["error_creation_team"], error, exc_info=True)

    def log_error_updating(self, error: str) -> None:
        self._logger.error(self._log_messages["error_updating_team"], error, exc_info=False)
