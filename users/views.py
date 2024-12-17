from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as c_prm
from orders.models import Order
from users import serializers
from users.models import CustomUser, CustomAuthToken, Team


class RegistrationView(generics.CreateAPIView, GenericViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.RegistrationSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.LoginSerializer

    def post(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")

        serializer = self.serializer_class(data={**request.data, "user_agent": user_agent})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        token, created = CustomAuthToken.objects.get_or_create(
            user=user,
            user_agent=user_agent,
        )
        if not created and not token.is_valid():
            token.delete()
            new_token = CustomAuthToken.objects.create(user=user, user_agent=user_agent)
            return Response({"token": new_token.key}, status=status.HTTP_200_OK)

        return Response({"token": token.key}, status=status.HTTP_201_CREATED)


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
    permission_classes = [c_prm.IsTeamMemberOrAdmin]
    serializer_class = serializers.TeamSerializer


class TeamsCreateView(generics.CreateAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsAdminOrStaff]
    serializer_class = serializers.CreateTeamSerializer

    def perform_create(self, serializer):
        serializer.save(leader=self.request.user)


class UpdateTeamView(generics.UpdateAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsAdminOrStaff, c_prm.IsTeamMemberOrAdmin]
    serializer_class = serializers.UpdateTeamSerializer


class TeamView(generics.RetrieveAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsTeamMemberOrAdmin]
    serializer_class = serializers.TeamSerializer

    def get_queryset(self):
        team_id = self.kwargs["pk"]
        return Team.objects.filter(pk=team_id).all()
