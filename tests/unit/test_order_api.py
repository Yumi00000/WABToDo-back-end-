import pytest
from rest_framework import status

from tests.test_data import order_fake_creating_data


class TestOrderAPI:

    @pytest.fixture(autouse=True)
    def setup(self, db, users, auth_base_client, unauthorized_client):
        # Users
        self.auth_client = auth_base_client
        self.unauthorized_client = unauthorized_client
        self.user, _ = users

        # Urls
        self.create_order_url = "/api/orders/create/"
        self.dashboard_url = "/api/users/dashboard/"
        self.edit_order_url = "/api/orders/edit/1/"
        self.order_not_found_url = "/api/orders/edit/2/"

    # --- Successful test cases ---
    def test_create_order(self):
        data = {**order_fake_creating_data}
        response = self.auth_client.post(self.create_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == 1
        assert response.data["owner"] == self.user[3].id
        assert response.data["name"] == order_fake_creating_data["name"]
        assert response.data["description"] == order_fake_creating_data["description"]
        assert response.data["deadline"] == order_fake_creating_data["deadline"]

    def test_get_all_user_orders(self, order):
        response = self.auth_client.get(self.dashboard_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == order.id
        assert response.data["results"][0]["owner"] == order.owner.first_name
        assert response.data["results"][0]["name"] == order.name

    def test_edit_order(self, order):
        data = {"name": "NewOrderName", "action": "pass"}
        response = self.auth_client.patch(self.edit_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == 1

    # --- Bad request test cases ---
    def test_create_order_bad_request(self):
        response = self.auth_client.post(self.create_order_url, data={}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_with_short_data(self):
        data = {"name": "New", "description": "description", "deadline": "2025-12-12"}
        response = self.auth_client.post(self.create_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_not_found(self):
        data = {"name": "NewOrderName"}
        response = self.auth_client.patch(self.order_not_found_url, data=data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_edit_order_bad_request(self, order):
        data = {"myordername": "OrderNewName"}
        response = self.auth_client.patch(self.edit_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- User unauthorized test cases ---
    def test_unauthorized_create_order(self):
        data = {**order_fake_creating_data}
        response = self.unauthorized_client.post(self.create_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_get_all_user_orders(self):
        response = self.unauthorized_client.get(self.dashboard_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_edit_order(self):
        response = self.unauthorized_client.patch(self.edit_order_url, data=order_fake_creating_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
