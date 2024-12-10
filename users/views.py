from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from orders.models import Order
from users import serializers
from users.models import CustomUser, CustomAuthToken, Team
from core import permissions as c_prm


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
        if token and token.is_valid():
            return Response({"token": token.key}, status=status.HTTP_200_OK)

        return Response({"token": token.key}, status=status.HTTP_201_CREATED)


class DashboardView(generics.ListAPIView, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.DashboardSerializer

    def get_queryset(self):
        user = self.request.user
        owner_orders = Q(owner=user)
        team_orders = Q(team__members__user=user)
        queryset = Order.objects.filter(owner_orders | team_orders).distinct()

        return queryset


class TeamsView(generics.ListAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsTeamMemberOrLeader]
    serializer_class = serializers.TeamSerializer
