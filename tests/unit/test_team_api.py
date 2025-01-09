import pytest
from rest_framework import status

from users.models import Team


class TestTeamApi:

    @pytest.fixture(autouse=True)
    def setup(self, db, users, auth_staff_client, auth_base_client, unauthorized_client):
        # Users
        self.user, _ = users
        self.staff_client = auth_staff_client
        self.base_client = auth_base_client
        self.unauthorized_client = unauthorized_client

        # Urls
        self.get_all_teams_url = "/api/users/teams/"
        self.get_team_details_url = "/api/users/team/info/1/"
        self.get_team_not_found_url = "/api/users/team/info/2/"
        self.create_team_url = "/api/users/team/create/"
        self.edit_team_url = "/api/users/team/edit/1/"
        self.edit_team_not_found_url = "/api/users/team/edit/2/"

    # --- Successful test cases ---
    def test_get_all_teams(self, team):
        response = self.staff_client.get(self.get_all_teams_url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_team_details(self, team):
        leader = self.user[0]
        list_of_members = [leader.username, self.user[1].username, self.user[2].username]
        response = self.staff_client.get(self.get_team_details_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["leader"] == leader.username
        assert response.data["list_of_members"] == list_of_members

    def test_create_team(self):
        list_of_members = [self.user[1].id, self.user[2].id]
        data = {"list_of_members": list_of_members}
        response = self.staff_client.post(self.create_team_url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["leader"] == self.user[0].username
        assert self.user[0].username in response.data["list_of_members"]
        assert self.user[1].username in response.data["list_of_members"]
        assert self.user[2].username in response.data["list_of_members"]

    def test_change_team_leader(self, team):
        data = {"leader_id": self.user[1].id, "list_of_members": [self.user[0].id, self.user[1].id, self.user[2].id]}
        response = self.staff_client.patch(self.edit_team_url, data=data, format="json")
        team_instance = Team.objects.get(id=1)

        assert response.status_code == status.HTTP_200_OK
        assert team_instance.leader_id == self.user[1].id
        assert response.data["leader"] == self.user[1].username
        assert self.user[0].username in response.data["list_of_members"]
        assert self.user[1].username in response.data["list_of_members"]
        assert self.user[2].username in response.data["list_of_members"]

    def test_change_team_members(self, team):
        data = {
            "leader_id": self.user[0].id,
            "list_of_members": [
                self.user[0].id,
                self.user[1].id,
            ],
        }
        response = self.staff_client.patch(self.edit_team_url, data=data, format="json")
        team_instance = Team.objects.get(id=1)

        print(team_instance.list_of_members.all())
        assert response.status_code == status.HTTP_200_OK
        assert team_instance.leader_id == self.user[0].id
        assert self.user[0] in team_instance.list_of_members.all()
        assert self.user[1] in team_instance.list_of_members.all()

    # --- Bad request test cases ---
    def test_create_team_bad_request(self):
        data = {}
        response = self.staff_client.post(self.create_team_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_edit_team_bad_request(self, team):
        data = {}
        response = self.staff_client.patch(self.edit_team_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_list_of_members(self, team):
        data = {"leader_id": self.user[0].id, "list_of_members": [None, None, None]}
        response = self.staff_client.patch(self.edit_team_url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- Base user has no permission ---
    def test_get_all_teams_without_permission(self, team):
        response = self.base_client.get(self.get_all_teams_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_team_details_without_permission(self, team):
        response = self.base_client.get(self.get_team_details_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "leader" not in response.data
        assert "list_of_members" not in response.data
        assert Team.objects.filter(id=1).exists() is True

    def test_create_without_permission(self):
        list_of_members = [self.user[1].id, self.user[2].id]
        data = {"list_of_members": list_of_members}
        response = self.base_client.post(self.create_team_url, data=data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "leader" not in response.data
        assert "list_of_members" not in response.data
        assert Team.objects.filter(id=1).exists() is False

    def test_edit_team_without_permission(self, team):
        data = {"leader_id": self.user[1].id, "list_of_members": [self.user[0].id, self.user[1].id, self.user[2].id]}
        response = self.base_client.patch(self.edit_team_url, data=data, format="json")
        team_instance = Team.objects.get(id=1)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "leader" not in response.data
        assert "list_of_members" not in response.data
        assert team_instance.leader_id != data["leader_id"]

    # --- User unauthorized test cases ---
    def test_get_all_teams_by_unauthorized_user(self, team):
        response = self.unauthorized_client.get(self.get_all_teams_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_team_details_by_unauthorized_user(self, team):
        response = self.unauthorized_client.get(self.get_team_details_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "leader" not in response.data
        assert "list_of_members" not in response.data
        assert Team.objects.filter(id=1).exists() is True

    def test_create_by_unauthorized_user(self):
        list_of_members = [self.user[1].id, self.user[2].id]
        data = {"list_of_members": list_of_members}
        response = self.unauthorized_client.post(self.create_team_url, data=data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "leader" not in response.data
        assert "list_of_members" not in response.data
        assert Team.objects.filter(id=1).exists() is False

    def test_edit_team_by_unauthorized_user(self, team):
        data = {"leader_id": self.user[1].id, "list_of_members": [self.user[0].id, self.user[1].id, self.user[2].id]}
        response = self.unauthorized_client.patch(self.edit_team_url, data=data, format="json")
        team_instance = Team.objects.get(id=1)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "leader" not in response.data
        assert "list_of_members" not in response.data
        assert team_instance.leader_id != data["leader_id"]
