import json
from urllib.parse import urljoin

import requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.db.models import Q
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as c_prm, settings
from orders.models import Order
from users import serializers as user_serializers
from users.mixins import UserLoggerMixin, TeamLoggerMixin
from users.models import CustomUser, CustomAuthToken, Team
from users.paginations import DashboardPagination

class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL
    client_class = OAuth2Client

class GoogleLoginCallback(APIView):
    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")
        
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Exchange code for access token
        token_url = f"{settings.SOCIAL_AUTH_GOOGLE_TOKEN_URL}?code={code}&client_id={settings.GOOGLE_OAUTH2_CLIENT_ID}&client_secret={settings.GOOGLE_OAUTH2_CLIENT_SECRET}&redirect_uri={settings.GOOGLE_OAUTH_CALLBACK_URL}&grant_type=authorization_code"

        response = requests.post(token_url)
        ensured_data_url = urljoin("http://localhost:8000", reverse("google_login"))

        response_login = requests.post(ensured_data_url, data={"access_token": response.json()["access_token"]})

        try:
            return Response(response_login, status=status.HTTP_200_OK)
        except CustomAuthToken.DoesNotExist:
            return Response({"detail": "Token not found."}, status=status.HTTP_404_NOT_FOUND)


class DashboardView(generics.ListAPIView, GenericViewSet, UserLoggerMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = user_serializers.DashboardSerializer
    pagination_class = DashboardPagination

    def get_queryset(self):
        user = self.request.user
        owner_orders = Q(owner=user)
        team_orders = Q(team__list_of_members=user)
        queryset = Order.objects.filter(owner_orders | team_orders).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        self.log_attempt_retrieve_dashboard()

        try:
            response = super().list(request, *args, **kwargs)
            self.log_successfully_retrieved_dashboard()
            return response

        except Exception as e:
            self.log_error_retrieving(str(e))
            response_error_message = {"error": "An error occurred while retrieving tasks."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamsListView(generics.ListAPIView, GenericViewSet, TeamLoggerMixin):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsTeamMemberOrAdmin]
    serializer_class = user_serializers.TeamSerializer

    def list(self, request, *args, **kwargs):
        self.log_attempt_retrieve_list_of_teams()

        try:
            response = super().list(request, *args, **kwargs)
            self.log_successfully_retrieved_list_of_teams()
            return response

        except Exception as e:
            self.log_error_retrieving(str(e))
            response_error_message = {"error": "An error occurred while retrieving lists of teams."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamsCreateView(generics.CreateAPIView, GenericViewSet, TeamLoggerMixin):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsAdminOrStaff]
    serializer_class = user_serializers.CreateTeamSerializer

    def create(self, request, *args, **kwargs):
        self.log_attempt_create_team()

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            team_data = serializer.save()  # This returns serialized data
            print(f"Response Data: {team_data}")  # Debug: Check the response
            return Response(team_data, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_error_creating(str(e))
            response_error_message = {"error": "An error occurred while creating new team"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateTeamView(generics.UpdateAPIView, GenericViewSet, TeamLoggerMixin):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsAdminOrStaff, c_prm.IsTeamMemberOrAdmin]
    serializer_class = user_serializers.UpdateTeamSerializer

    def update(self, request, *args, **kwargs):
        self.log_attempt_update_team()

        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save()
            return Response(updated_instance)

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_error_updating(str(e))
            response_error_message = {"error": "An error occurred while updating the team"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamView(generics.RetrieveAPIView, GenericViewSet, TeamLoggerMixin):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsTeamMemberOrAdmin]
    serializer_class = user_serializers.TeamSerializer

    def get_queryset(self):
        team_id = self.kwargs["pk"]
        return Team.objects.filter(pk=team_id).all()

    def get(self, request, *args, **kwargs):
        self.log_attempt_retrieve_team_details()

        try:
            response = super().get(request, *args, **kwargs)
            self.log_successful_retrieve_team_details()
            return response

        except Exception as e:
            self.logg_error_retrieving_details(str(e))
            response_error_message = {"error": "An error occurred while retrieving the team details"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
