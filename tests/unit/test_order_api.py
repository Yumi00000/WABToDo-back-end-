from rest_framework import status
from rest_framework.test import APITransactionTestCase, APIClient

from orders.models import Order
from users.models import CustomUser, CustomAuthToken
from core.constants import ORDER_FAKE_CREATING_DATA


class TestOrderApi(APITransactionTestCase):
    def setUp(self):
        # Urls
        self.create_order_url = "/api/orders/create/"
        self.dashboard_url = "/api/users/dashboard/"
        self.edit_order_url = "/api/orders/edit/1/"

        # Authorization
        self.user_credentials = {"id": 1, "username": "testuser", "password": "testpassword"}
        self.user = CustomUser.objects.create_user(**self.user_credentials)
        self.token, created = CustomAuthToken.objects.get_or_create(user=self.user, user_agent="TestAgent")

        # Users
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.key}")
        self.unauthorized_client = APIClient()

        # Orders
        self.order = Order.objects.create(owner_id=self.user.id, **ORDER_FAKE_CREATING_DATA)

    def test_create_order(self):
        response = self.client.post(self.create_order_url, data={**ORDER_FAKE_CREATING_DATA}, format="json")
        print("Response data:", response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["owner"] == self.user.id
        assert response.data["name"] == ORDER_FAKE_CREATING_DATA["name"]
        assert response.data["description"] == ORDER_FAKE_CREATING_DATA["description"]
        assert response.data["deadline"] == ORDER_FAKE_CREATING_DATA["deadline"]

    def test_get_all_user_orders(self):
        response = self.client.get(self.dashboard_url)
        print("Response data:", response.data["results"][0]["owner"])
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_create_order_bad_request(self):
        response = self.client.post(self.create_order_url, data={}, format="json")
        print("Response data:", response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_with_short_data(self):
        response = self.client.post(
            self.create_order_url,
            data={"name": "New", "description": "description", "deadline": "2025-12-12"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthorized_create_order(self):
        response = self.unauthorized_client.post(
            self.create_order_url, data={**ORDER_FAKE_CREATING_DATA}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_get_all_user_orders(self):
        response = self.unauthorized_client.get(self.dashboard_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_edit_order(self):
        response = self.unauthorized_client.patch(self.edit_order_url, data={**ORDER_FAKE_CREATING_DATA})
        assert response.status_code == status.HTTP_403_FORBIDDEN
