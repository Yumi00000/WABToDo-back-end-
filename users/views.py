import logging
from urllib.parse import urljoin

import requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as c_prm, settings
from orders.models import Order
from users import serializers
from users.models import CustomAuthToken, Team


####?????####Maybe can be removed####?????####

# class RegistrationView(generics.CreateAPIView, GenericViewSet):
#     queryset = CustomUser.objects.all()
#     permission_classes = [permissions.AllowAny]
#     serializer_class = serializers.RegistrationSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#
#         if serializer.is_valid():
#             serializer.save(request=request)
#         return Response({"detail": "User registered successfully!"}, status=201)



####?????####Maybe can be removed####?????####

# class LoginView(APIView):
#     permission_classes = [permissions.AllowAny]
#     serializer_class = serializers.CustomLoginSerializer
#
#     def post(self, request, *args, **kwargs):
#         user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")
#
#         serializer = self.serializer_class(data={**request.data, "user_agent": user_agent})
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#         user = serializer.validated_data["user"]
#         token, created = CustomAuthToken.objects.get_or_create(
#             user=user,
#             user_agent=user_agent,
#         )
#         if token and token.is_valid():
#             return Response({"token": token.key}, status=status.HTTP_200_OK)
#
#         return Response({"token": token.key}, status=status.HTTP_201_CREATED)

####?????####Maybe can be removed####?????####
# class LogoutView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     logger = logging.getLogger()
#
#     def post(self, request):
#         user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")
#         try:
#             token = CustomAuthToken.objects.get(user=request.user, user_agent=user_agent)
#             token.status = "Offline"
#             token.save()
#
#             self.logger.info("The user logged out successfully")
#             return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
#
#         except CustomAuthToken.DoesNotExist:
#             self.logger.error("Invalid token")
#             return Response({"detail": "Token not found."}, status=status.HTTP_404_NOT_FOUND)


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


class DashboardView(generics.ListAPIView, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.DashboardSerializer

    def get_queryset(self):
        user = self.request.user
        owner_orders = Q(owner=user)
        team_orders = Q(team__list_of_members=user)
        queryset = Order.objects.filter(owner_orders | team_orders).distinct()

        return queryset


class TeamsListView(generics.ListAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsTeamMemberOrLeader]
    serializer_class = serializers.TeamSerializer


class TeamsCreateView(generics.CreateAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [permissions.IsAuthenticated, c_prm.IsAdminOrStaff]
    serializer_class = serializers.CreateTeamSerializer

    def perform_create(self, serializer):
        serializer.save(leader=self.request.user)


class UpdateTeamView(generics.UpdateAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsAdminOrStaff, c_prm.IsTeamMemberOrLeader]
    serializer_class = serializers.UpdateTeamSerializer


class TeamView(generics.RetrieveAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [permissions.IsAuthenticated, c_prm.IsTeamMemberOrLeader]
    serializer_class = serializers.TeamSerializer

    def get_queryset(self):
        team_id = self.kwargs["pk"]
        return Team.objects.filter(pk=team_id).all()
