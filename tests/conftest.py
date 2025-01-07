import pytest
from django.conf import settings
from rest_framework.test import APIClient

from core.constants import ORDER_FAKE_CREATING_DATA
from orders.models import Order
from tasks.models import Task
from users.models import CustomAuthToken, Team
from users.models import CustomUser


@pytest.fixture(scope="session")
def db_settings():
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    }


@pytest.fixture(scope="session")
def users(django_db_setup, django_db_blocker) -> tuple[list[CustomUser], list[dict]]:
    with django_db_blocker.unblock():
        user_credentials = [
            {
                "id": 1,
                "username": "testuser1",
                "first_name": "John",
                "last_name": "Doe",
                "password": "testpassword",
                "is_team_member": True,
                "is_admin": True,
                "is_staff": True,
            },
            {
                "id": 2,
                "username": "testuser2",
                "first_name": "Bob",
                "last_name": "Doe",
                "password": "testpassword",
                "is_team_member": True,
            },
            {
                "id": 3,
                "username": "testuser3",
                "first_name": "Mark",
                "last_name": "Doe",
                "password": "testpassword",
                "is_team_member": True,
            },
            {"id": 4, "username": "testuser4", "first_name": "Bob2", "last_name": "Doe", "password": "testpassword"},
        ]
        user = [CustomUser.objects.create_user(**credentials) for credentials in user_credentials]
        return user, user_credentials


@pytest.fixture
def auth_staff_client(users) -> APIClient:
    instance, _ = users
    token, _ = CustomAuthToken.objects.get_or_create(user=instance[0], user_agent="TestAgent")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@pytest.fixture
def auth_base_client(users) -> APIClient:
    instance, _ = users
    token, _ = CustomAuthToken.objects.get_or_create(user=instance[3], user_agent="TestAgent")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@pytest.fixture
def unauthorized_client() -> APIClient:
    return APIClient()


@pytest.fixture
def order(users) -> Order:
    instance, _ = users
    return Order.objects.create(owner=instance[3], **ORDER_FAKE_CREATING_DATA)


@pytest.fixture
def team(users, order) -> Team:
    instance, _ = users
    team = Team.objects.create(id=1, leader=instance[0])
    team.list_of_members.add(*instance[1:3])
    team.save()

    order.team = team
    order.status = "active"
    order.save()

    return team


@pytest.fixture
def task(users, team, order) -> Task:
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
