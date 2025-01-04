from rest_framework.test import APITransactionTestCase, APIClient

from users.models import CustomUser


class TestOrderApi(APITransactionTestCase):
    def setUp(self):
        # Urls
        self.create_order_url = "/api/orders/create/"

        # Users
        self.user_credentials = {"username": "testuser", "password": "testpassword"}
        self.user = CustomUser.objects.create_user(**self.user_credentials)
        self.client.login(**self.user_credentials)
        self.unauthorized_client = APIClient()

    def test_create_order_bad_request(self):
        response = self.client.post(self.create_order_url, data={}, format="json")
        assert response.status_code == 400

    def test_create_order_with_short_data(self):
        response = self.client.post(
            self.create_order_url,
            data={"name": "New", "description": "description", "deadline": "2025-12-12"},
            format="json",
        )
        assert response.status_code == 400
