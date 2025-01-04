import pytest
from django.conf import settings
from rest_framework.test import APIClient

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


@pytest.fixture()
def create_user(db_settings):
    def _create_user(username="testuser", password="testpassword"):
        return CustomUser.objects.create_user(username=username, password=password, is_active=True)

    return _create_user


@pytest.fixture()
def get_token(create_user):
    def _get_token(username="testuser", password="testpassword", user_agent="testagent"):
        user = create_user(username=username, password=password)
        client = APIClient()
        response = client.post(
            "/api/users/login/", {"username": username, "password": password}, HTTP_USER_AGENT=user_agent
        )
        assert response.status_code in [200, 201]
        return response.data["token"], user

    return _get_token


@pytest.fixture()
def authorized_client(get_token):
    def _authorized_client(username="testuser", password="testpassword"):
        token, user = get_token(username=username, password=password)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client, user

    return _authorized_client
