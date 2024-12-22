from django.db.models import Q
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as c_prm
from orders.models import Order
from users import serializers as user_serializers
from users.mixins import UserLoggerMixin, TeamLoggerMixin
from users.models import CustomUser, CustomAuthToken, Team
from users.paginations import DashboardPagination


class RegistrationView(generics.CreateAPIView, GenericViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = user_serializers.RegistrationSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = user_serializers.LoginSerializer

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

    def perform_create(self, serializer):
        serializer.save(leader=self.request.user)

    def create(self, request, *args, **kwargs):
        self.log_attempt_create_team()

        try:
            response = super().create(request, *args, **kwargs)
            self.log_successfully_created()
            return response

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
            response = super().update(request, *args, **kwargs)
            self.log_successfully_updated()
            return response

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
