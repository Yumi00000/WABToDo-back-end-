from django.core.signing import Signer, BadSignature
from django.db.models import Q
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as c_prm
from orders.models import Order
from users import serializers as user_serializers
from users.mixins import UserLoggerMixin, TeamLoggerMixin
from users.models import CustomAuthToken, Team, CustomUser
from users.paginations import DashboardPagination
from users.utils import send_activation_email


class RegistrationView(generics.CreateAPIView, GenericViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = user_serializers.RegistrationSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().get(email=response.data["email"])
        print(user)
        send_activation_email(request, user)
        return response


class ActivateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, user_signed):
        signer = Signer()
        try:
            print(user_signed)
            user_id = signer.unsign(user_signed)
            print(user_id)
            user = CustomUser.objects.get(id=user_id)
        except (BadSignature, CustomUser.DoesNotExist):
            return Response({"detail": "Invalid or expired link"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        return Response({"detail": "Account successfully activated"}, status=status.HTTP_200_OK)


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
        if not created:
            if token.is_valid():
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            token.delete()

        token = CustomAuthToken.objects.create(user=user, user_agent=user_agent)

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
