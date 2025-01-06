import pytest
from rest_framework import status

from core.constants import ORDER_FAKE_CREATING_DATA


class TestOrderAPI:

    @pytest.fixture(autouse=True)
    def setup(self, db, user, auth_client, unauthorized_client):
        # Users
        self.auth_client = auth_client
        self.unauthorized_client = unauthorized_client
        self.user = user

        # Urls
        self.create_order_url = "/api/orders/create/"
        self.dashboard_url = "/api/users/dashboard/"
        self.edit_order_url = "/api/orders/edit/1/"
        self.order_not_found_url = "/api/orders/edit/2/"

    def test_db(self, db, db_settings):
        assert db == db_settings

    def test_create_order(self):
        data = {**ORDER_FAKE_CREATING_DATA}
        response = self.auth_client.post(self.create_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == 1
        assert response.data["owner"] == self.user[0].id
        assert response.data["name"] == ORDER_FAKE_CREATING_DATA["name"]
        assert response.data["description"] == ORDER_FAKE_CREATING_DATA["description"]
        assert response.data["deadline"] == ORDER_FAKE_CREATING_DATA["deadline"]

    def test_get_all_user_orders(self, order):
        response = self.auth_client.get(self.dashboard_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == order.id
        assert response.data["results"][0]["owner"] == order.owner.first_name
        assert response.data["results"][0]["name"] == order.name

    def test_edit_order(self, order):
        data = {"name": "NewOrderName"}
        response = self.auth_client.patch(self.edit_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK

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

    def test_unauthorized_create_order(self):
        data = {**ORDER_FAKE_CREATING_DATA}
        response = self.unauthorized_client.post(self.create_order_url, data=data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_get_all_user_orders(self):
        response = self.unauthorized_client.get(self.dashboard_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_edit_order(self):
        response = self.unauthorized_client.patch(self.edit_order_url, data=ORDER_FAKE_CREATING_DATA)

        assert response.status_code == status.HTTP_403_FORBIDDEN
