from django.contrib.auth import login
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as c_prm
from core.service import GoogleRawLoginFlowService
from orders.models import Order
from users import serializers
from users.models import CustomAuthToken, Team, Chat, CustomUser


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team_data = serializer.save()  # This returns serialized data
        print(f"Response Data: {team_data}")  # Debug: Check the response
        return Response(team_data, status=status.HTTP_201_CREATED)


class UpdateTeamView(generics.UpdateAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsAdminOrStaff, c_prm.IsTeamMemberOrAdmin]
    serializer_class = serializers.UpdateTeamSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        return Response(updated_instance)


class TeamView(generics.RetrieveAPIView, GenericViewSet):
    queryset = Team.objects.all()
    permission_classes = [c_prm.IsTeamMemberOrAdmin]
    serializer_class = serializers.TeamSerializer

    def get_queryset(self):
        team_id = self.kwargs["pk"]
        return Team.objects.filter(pk=team_id).all()


class CreateChatView(generics.CreateAPIView, GenericViewSet):
    queryset = Chat.objects.all()
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = serializers.CreateChatSerializer


class GoogleLoginApi(APIView):
    serializer_class = serializers.InputSerializer

    def get(self, request, *args, **kwargs):
        input_serializer = self.serializer_class(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get("code")
        error = validated_data.get("error")
        state = validated_data.get("state")

        if error is not None:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST
            )

        if code is None or state is None:
            return Response(
                {"error": "Code and state are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        session_state = request.session.get("google_oauth2_state")

        if session_state is None:
            return Response(
                {"error": "CSRF check failed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        del request.session["google_oauth2_state"]

        if state != session_state:
            return Response(
                {"error": "CSRF check failed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        google_login_flow = GoogleRawLoginFlowService()

        google_tokens = google_login_flow.get_tokens(code=code)

        id_token_decoded = google_tokens.decode_id_token()
        user_info = google_login_flow.get_user_info(google_tokens=google_tokens)

        user_email = id_token_decoded["email"]

        user, created = CustomUser.objects.get_or_create(
            email=user_email,
            defaults={"username": id_token_decoded.get("name"), "google_id": id_token_decoded.get("sub")}
        )

        CustomAuthToken.objects.create(user=user)
        if user is None:
            return Response(
                {"error": f"User with email {user_email} is not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        login(request, user)

        result = {
            "id_token_decoded": id_token_decoded,
            "user_info": user_info,
        }

        return Response(result)
