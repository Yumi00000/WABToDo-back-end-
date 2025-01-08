import pytest
from django.core.signing import Signer
from rest_framework import status

from users.models import CustomUser, CustomAuthToken
from tests.test_data import registration_credentials


class TestRegistration:
    @pytest.fixture(autouse=True)
    def setup(self, db, unauthorized_client):
        self.client = unauthorized_client
        self.registration_url = "/api/users/registration/"

    # --- Successful test cases ---
    def test_registration_sends_activation_email(self, mock_send_email_task):
        data = registration_credentials
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == data["username"]
        assert response.data["email"] == data["email"]

        mock_send_email_task.assert_called_once()
        user = CustomUser.objects.get(email=data["email"])
        args, kwargs = mock_send_email_task.call_args
        sent_email = args[0]
        signed_url = args[1]

        assert sent_email == user.email

        signer = Signer()
        expected_signed_id = signer.sign(user.id)
        assert expected_signed_id in signed_url

    # --- Bad request test cases ---
    def test_registration_bad_request(self):
        data = registration_credentials
        data["password"] = None
        data["password2"] = None

        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_too_short(self):
        data = registration_credentials
        data["password"] = "Bnn1!"
        data["password2"] = "Bnn1!"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_has_no_capital_letter(self):
        data = registration_credentials
        data["password"] = "weneedmorebananasthan1!!!"
        data["password2"] = "weneedmorebananasthanone!!!"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_has_no_numbers(self):
        data = registration_credentials
        data["password"] = "Weneedmorebananasthanone!!!"
        data["password2"] = "Weneedmorebananasthanone!!!"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_has_username(self):
        data = registration_credentials
        data["password"] = "Thefirstuserpassword!!!"
        data["password2"] = "Thefirstuserpassword!!!"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_has_first_or_last_name(self):
        data = registration_credentials
        data["password"] = "Userpasswordbutiamnotuser!!!"
        data["password2"] = "Userpasswordbutiamnotuser!!!"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_has_email(self):
        data = registration_credentials
        data["password"] = "Theuseremail@gmail.comtheuseremail@gmail.com!!!"
        data["password2"] = "Theuseremail@gmail.comtheuseremail@gmail.com!!!"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_has_spaces(self):
        data = registration_credentials
        data["password"] = "Weneedmorebananas than1!!!"
        data["password2"] = "Weneedmorebananas than1!!!"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_username_already_exist(self):
        data = registration_credentials
        data["username"] = "testuser1"
        response = self.client.post(self.registration_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    @pytest.fixture(autouse=True)
    def setup(self, db, unauthorized_client):
        self.client = unauthorized_client

        self.login_url = "/api/users/login/"

    # --- Successful test cases ---
    def test_login(self, users):
        data = {"username": "testuser1", "password": "testpassword"}
        user = CustomUser.objects.get(username=data["username"])

        response = self.client.post(self.login_url, data=data, format="json")
        token = CustomAuthToken.objects.get(user_id=user.id)

        assert user.is_active is True
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["token"] == token.key

    # --- Bad request test cases ---
    def test_login_invalid_credentials(self, users):
        data = {"username": "user1", "password": "testpassword"}
        response = self.client.post(self.login_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_is_not_active(self, users):
        data = {"username": "testuser5", "password": "testpassword"}
        response = self.client.post(self.login_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
