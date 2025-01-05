import pytest
from django.conf import settings
from rest_framework.test import APIClient

from core.constants import ORDER_FAKE_CREATING_DATA
from orders.models import Order
from users.models import CustomAuthToken
from users.models import CustomUser


@pytest.fixture(scope="session")
def db_settings():
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_crm_lab_database",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "ATOMIC_REQUESTS": True,
    }


@pytest.fixture
def user(db) -> tuple[CustomUser, dict]:
    credentials = {
        "id": 1,
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "password": "testpassword",
    }
    user = CustomUser.objects.create_user(**credentials)
    return user, credentials


@pytest.fixture
def auth_client(user) -> APIClient:
    user, _ = user
    token, _ = CustomAuthToken.objects.get_or_create(user=user, user_agent="TestAgent")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@pytest.fixture
def unauthorized_client() -> APIClient:
    return APIClient()


@pytest.fixture
def order(user: tuple[CustomUser, dict]) -> Order:
    user, _ = user
    return Order.objects.create(owner=user, **ORDER_FAKE_CREATING_DATA)
