from unittest.mock import patch

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from orders.models import Order
from tasks.models import Task
from tests.test_data import user_credentials, order_fake_creating_data
from users.models import CustomAuthToken, Team
from users.models import CustomUser


# --- Users initialization ---
@pytest.fixture(scope="session")
def users(django_db_setup, django_db_blocker) -> tuple[list[CustomUser], list[dict]]:
    """
    Creates and returns a tuple containing:
    - A list of `CustomUser` instances created in the database.
    - A list of dictionaries with user credentials used for creation.
    Useful for testing scenarios involving authenticated or unauthenticated users.
    """
    with django_db_blocker.unblock():
        user = [CustomUser.objects.create_user(**credentials) for credentials in user_credentials]
        return user, user_credentials


@pytest.fixture
def auth_staff_client(users) -> APIClient:
    """
    Returns an API client authenticated as a staff user (with elevated permissions).
    Staff user is retrieved from the list of created users.
    """
    instance, _ = users
    token, _ = CustomAuthToken.objects.get_or_create(user=instance[0], user_agent="TestAgent")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@pytest.fixture
def auth_base_client(users) -> APIClient:
    """
    Returns an API client authenticated as a basic user (with limited permissions).
    Basic user is retrieved from the list of created users.
    """
    instance, _ = users
    token, _ = CustomAuthToken.objects.get_or_create(user=instance[3], user_agent="TestAgent")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@pytest.fixture
def unauthorized_client() -> APIClient:
    """
    Returns an API client without authentication credentials.
    Useful for testing access control and unauthorized request handling.
    """
    return APIClient()


# --- Main testing objects ---
@pytest.fixture
def order(users) -> Order:
    """
    Creates and returns an `Order` instance.
    The owner of the order is a basic user retrieved from the list of created users.
    """
    instance, _ = users
    return Order.objects.create(owner=instance[3], **order_fake_creating_data)


@pytest.fixture
def team(users, order) -> Team:
    """
    Creates and returns a `Team` instance with the following setup:
    - A leader is assigned as the first user from the created users.
    - Other users are added as members of the team.
    - The given order is associated with the team and marked as "active".
    """
    instance, _ = users
    team = Team.objects.create(id=1, leader=instance[0])
    team.list_of_members.add(*instance[0:3])
    team.save()

    order.team = team
    order.status = "active"
    order.save()

    return team


@pytest.fixture
def task(users, team, order) -> Task:
    """
    Creates and returns a `Task` instance with the following setup:
    - Associated with the given team and order.
    - Assigned to a specific user as the executor.
    - Default status is set to "active".
    """
    instance, _ = users
    return Task.objects.create(
        id=1,
        title="Test Task",
        description="Test description",
        deadline="2026-12-12",
        executor=instance[1],
        team=team,
        order=order,
        status="active",
    )


# --- Fixtures for utils ---
@pytest.fixture
def mock_send_email_task():
    """
    A mock fixture to replace the `send_email.delay` method during testing.

    This mock serves the following purposes:
    1. Prevents the actual execution of the `send_email` Celery task.
    2. Captures arguments passed to `send_email.delay` for validation in tests.
    3. Provides control over the return value of the mocked method, if required.

    Usage:
        - Use `mock_send_email_task.assert_called_once()` to verify it was called.
        - Access `mock_send_email_task.call_args` to inspect arguments passed during the call.
    """
    with patch("users.tasks.send_email.delay") as mock_task:
        yield mock_task
