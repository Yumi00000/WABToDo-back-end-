import pytest
from django.core.signing import Signer
from rest_framework import status
from django.core import mail
from tests.test_data import registration_credentials
from users.models import CustomUser


class TestRegistration:
    @pytest.fixture(autouse=True)
    def setup(self, db, unauthorized_client):
        self.client = unauthorized_client
        self.registration_url = "/api/users/registration/"

    def test_registration_email_content(self):
        data = registration_credentials
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == data["username"]
        assert response.data["email"] == data["email"]

        assert len(mail.outbox) == 1
        user = CustomUser.objects.get(email=data["email"])
        email = mail.outbox[0]

        assert email.to == [user.email]
        assert "Registration complete" in email.subject
        assert str(user.id) in email.body

    def test_full_registration_flow(self):
        data = registration_credentials
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == data["username"]
        assert response.data["email"] == data["email"]

        user = CustomUser.objects.get(email=data["email"])
        user_signed = Signer().sign(user.id)
        activation_url = f"/api/users/activate/{user_signed}"
        activation_response = self.client.get(activation_url)

        assert activation_response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_active is True
