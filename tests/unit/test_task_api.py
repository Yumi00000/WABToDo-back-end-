import pytest
from rest_framework import status


class TestTaskApi:

    @pytest.fixture(autouse=True)
    def setup(self, db, users, auth_staff_client, unauthorized_client):
        # Users
        self.auth_client = auth_staff_client
        self.unauthorized_client = unauthorized_client
        self.user, _ = users

        # Urls
        self.get_tasks_url = f"/api/tasks/"
        self.create_task_url = f"/api/tasks/create/"
        self.edit_task_url = f"/api/tasks/edit/1/"
        self.task_not_found_url = f"/api/tasks/edit/2/"
        self.delete_task_url = f"/api/tasks/delete/1/"

    # --- Successful test cases ---
    def test_create_task(self, team, order):
        data = {
            "title": "test title",
            "description": "test description",
            "executor": self.user[1].id,
            "deadline": "2026-12-12",
        }
        response = self.auth_client.post(self.create_task_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == 1
        assert response.data["title"] == data["title"]
        assert response.data["executor"] == data["executor"]
        assert response.data["order"] == order.id
        assert response.data["team"] == team.id

    def test_get_team_tasks(self, task, team):
        params = {
            "teamId": team.id,
        }
        response = self.auth_client.get(self.get_tasks_url, params=params)
        print(response.data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["team"] == team.id
        assert response.data["results"][0]["status"] == "active"
        assert response.data["results"][0]["executor"] == task.executor.id

    def test_edit_task(self, task, team):
        data = {"title": "testTitle", "description": "testNewDescription", "deadline": "2026-10-12"}
        response = self.auth_client.patch(self.edit_task_url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == 1
        assert response.data["title"] == "testTitle"

    def test_change_task_executor(self, task, team):
        data = {"executor": self.user[0].id}
        response = self.auth_client.patch(self.edit_task_url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["executor"] == data["executor"]

    def test_delete_task(self, task, team):
        response = self.auth_client.delete(self.delete_task_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    # --- Bad request test cases ---
    def test_create_task_bad_request(self, team):
        response = self.auth_client.post(self.create_task_url, data={}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_edit_task_bad_request(self, task, team):
        data = {"title": "T"}
        response = self.auth_client.patch(self.edit_task_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_wrong_executor_for_task(self, task, team):
        data = {"executor": self.user[3].id}
        response = self.auth_client.patch(self.edit_task_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_is_not_team_member(self, task, team, auth_base_client):
        get_params = {"teamId": team.id}
        create_data = {
            "title": "test title",
            "description": "test description",
            "executor": self.user[1].id,
            "deadline": "2026-12-12",
        }
        edit_data = {"title": "testTitle", "description": "testNewDescription", "deadline": "2026-10-12"}

        get_response = auth_base_client.get(self.get_tasks_url, params=get_params)
        create_response = auth_base_client.post(self.create_task_url, data=create_data, format="json")
        edit_response = auth_base_client.patch(self.edit_task_url, data=edit_data, format="json")
        delete_response = auth_base_client.delete(self.delete_task_url)

        assert get_response.status_code == status.HTTP_403_FORBIDDEN
        assert create_response.status_code == status.HTTP_403_FORBIDDEN
        assert edit_response.status_code == status.HTTP_403_FORBIDDEN
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN

    # --- User unauthorized test cases ---
    def test_unauthorized_get_requests(self):
        get_params = {"teamId": 1}
        get_response = self.unauthorized_client.get(self.get_tasks_url, params=get_params)

        assert get_response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_post_requests(self):
        data = {
            "title": "test title",
            "description": "test description",
            "executor": self.user[1].id,
            "deadline": "2026-12-12",
        }
        get_response = self.unauthorized_client.get(self.create_task_url, data=data)

        assert get_response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_edit_requests(self):
        data = {"title": "testTitle", "description": "testNewDescription", "deadline": "2026-10-12"}
        get_response = self.unauthorized_client.get(self.get_tasks_url, data=data)

        assert get_response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthorized_delete_requests(self):
        get_response = self.unauthorized_client.get(self.delete_task_url)

        assert get_response.status_code == status.HTTP_403_FORBIDDEN
