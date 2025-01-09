from autobahn.util import generate_user_password
from django.contrib.auth import login
from django.core.signing import Signer, BadSignature
from django.db.models import Q
from django.http import response as dj_res
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import permissions as c_prm
from core.service import GoogleRawLoginFlowService
from orders.models import Order
from users import serializers as user_serializers
from users.mixins import UserLoggerMixin, TeamLoggerMixin
from users.models import CustomAuthToken
from users.models import Participant
from users.models import Team, Chat, CustomUser
from users.paginations import DashboardPagination
from users.utils import send_activation_email, TokenManager


class RegistrationView(generics.CreateAPIView, GenericViewSet):
    """
    Handles user registration functionalities.

    This class combines functionality from `CreateAPIView` and `GenericViewSet` to allow
    registration of new users in the system. It interacts with the CustomUser model
    and uses a designated serializer to handle the creation process. After successfully
    creating a user, it sends an activation email to the registered email address.

    Attributes:
        queryset: Specifies the queryset of `CustomUser` instances.
        permission_classes: List of permissions required to access this view, allowing
            any client to register without restrictions.
        serializer_class: Specifies the serializer used for processing registration data.
    """
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = user_serializers.RegistrationSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().get(email=response.data["email"])
        send_activation_email(request, user)
        return response


class ActivateView(APIView):
    """
    Class to handle user account activation process.

    This class is responsible for activating a user's account through a predefined
    signed URL. It verifies the signed data, retrieves the corresponding user, and
    activates their account if valid.

    Attributes:
        permission_classes (list): List of permissions required to access this view.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, user_signed):
        signer = Signer()
        try:
            user_id = signer.unsign(user_signed)
            user = CustomUser.objects.get(id=user_id)
        except (BadSignature, CustomUser.DoesNotExist):
            return Response({"detail": "Invalid or expired link"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        return Response({"detail": "Account successfully activated"}, status=status.HTTP_200_OK)


class LoginView(APIView, TokenManager):
    """
    Handles user login functionality.

    The LoginView class facilitates user login by validating the provided credentials
    and generating a token for the authenticated user. It combines functionality
    from APIView for handling requests and TokenManager for managing user tokens.
    This class allows any user to access the endpoint regardless of authentication
    status due to its permission settings.

    Attributes:
        permission_classes (list): Specifies the permission classes to allow
            unrestricted access to the login endpoint.
        serializer_class (type): Defines the serializer class to validate
            and process login data.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = user_serializers.LoginSerializer

    def post(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")

        serializer = self.serializer_class(data={**request.data, "user_agent": user_agent})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        token, created = self.get_or_create_token(user, user_agent)

        return Response(
            {"token": token.key},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class EditUserView(generics.RetrieveUpdateAPIView, GenericViewSet):
    """
    This class is a view for retrieving and updating user information.

    The EditUserView class provides functionality to retrieve and update
    information of a user. It combines the capabilities of RetrieveUpdateAPIView
    with additional behavior from GenericViewSet. This class enforces permissions
    to ensure that only the account owner can access or modify their data.
    A specific serializer is used to handle the transformation between serialized
    and database representations of the user's data.

    Attributes:
        queryset: A queryset to retrieve all CustomUser instances.
        permission_classes: A list of permission classes, restricting access
            to account owners only.
        serializer_class: The serializer class responsible for transforming
            user data between representations.
    """
    queryset = CustomUser.objects.all()
    permission_classes = [c_prm.IsAccountOwner]
    serializer_class = user_serializers.EditUserSerializer


class DashboardView(generics.ListAPIView, GenericViewSet, UserLoggerMixin):
    """
    Class DashboardView is responsible for handling API requests related to the user's dashboard.

    This class provides functionality for authenticated users to retrieve information regarding their own orders
    and those of their team members. It combines functionality of Django Rest Framework's ListAPIView and
    GenericViewSet to handle listing operations. Additionally, it includes custom logging capabilities to track
    dashboard access and actions.

    Attributes:
        permission_classes (list): Defines the permissions required to access this view.
        serializer_class (type): The serializer class used to serialize the response data.
        pagination_class (type): The pagination class defining how the data is paginated.

    Methods:
        get_queryset():
            Retrieves the queryset containing orders that belong to the logged-in user or to their team members.

        list():
            Handles listing operation along with custom logging of actions and error handling.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = user_serializers.DashboardSerializer
    pagination_class = DashboardPagination

    def get_queryset(self):
        user = self.request.user
        owner_orders = Q(owner=user)
        team_orders = Q(team__list_of_members=user)
        queryset = Order.objects.filter(owner_orders | team_orders).distinct()

        return queryset.order_by("created_at")

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
    """
    Handles listing Team objects with logging and permission checking.

    This class is a custom implementation for handling requests to retrieve
    a list of Team objects. It adds logging capabilities to track successful
    retrievals, failed attempts, and errors during the process. This class
    utilizes Django REST framework functionality for generic listing of objects
    and specifically works with Team objects.

    Attributes:
        queryset: The base queryset containing all Team objects.
        permission_classes: A list of permission classes applied to the view.
        serializer_class: Specifies the serializer used to serialize Team objects.

    Methods:
        list:
            Handles GET requests to retrieve a list of team objects. Logs actions
            such as retrieval attempts, success, and errors during execution.

    Raises:
        Exception: Catches and logs any exception that occurs during the retrieval
        and returns an HTTP 500 response with an error message.
    """
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
    """
    Handles the creation of new team records in the system.

    This view combines functionalities of Django Rest Framework's CreateAPIView and GenericViewSet.
    It also incorporates custom logging mechanics from TeamLoggerMixin to log specific actions related
    to team creation. Primarily, it facilitates accepting, validating, and storing new team-related
    data via HTTP POST requests.

    Attributes:
        queryset: Queryset used to retrieve Team objects from the database.
        permission_classes: List of permission classes that restrict access to the view to admins or staff members.
        serializer_class: Serializer class used to validate and serialize the input data for team creation.

    Methods:
        create: Handles HTTP POST requests to create a new team.
    """
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
    """
    Provides functionality for updating team details.

    This class is designed to handle HTTP PATCH or PUT requests to update existing team
    details. It combines functionality from `UpdateAPIView`, `GenericViewSet`, and a custom
    mixin `TeamLoggerMixin`. The permissions include both administrative controls and access
    checks to ensure that only authorized users may update a team. The serializer used
    validates and applies the update logic. Logging is enabled throughout the process to
    track events, errors, and validation issues.

    Attributes:
        queryset: The complete set of Team objects to support retrieving instances for updating.
        permission_classes: A list of permission classes that enforce rules for access to the endpoint.
        serializer_class: Specifies the serializer used to handle validation and update operations.
    """
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

        except dj_res.Http404:
            self.log_validation_error("Task not found")
            raise
        except Exception as e:
            self.log_error_updating(str(e))
            response_error_message = {"error": "An error occurred while updating the team"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamView(generics.RetrieveAPIView, GenericViewSet, TeamLoggerMixin):
    """
    Retrieve and manage team details through a view.

    This class extends Django REST framework's `RetrieveAPIView` to enable retrieval of team
    details. It also incorporates additional functionality such as logging actions performed
    during the retrieval process and managing permissions for team members or administrators.

    Attributes:
        queryset: The initial queryset containing all team objects from the database.
        permission_classes: A list of permission classes, ensuring only team members or
            administrators have access to the view.
        serializer_class: The serializer class used for converting team objects into
            serializable representations.

    Methods:
        get_queryset():
            Override to filter the queryset based on the team ID provided in the request.

        get():
            Handle GET requests, log retrieval attempts and results, and handle errors
            gracefully during the team detail retrieval process.
    """
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


class CreateChatView(generics.CreateAPIView, GenericViewSet):
    """
    This class handles the creation of chat instances.

    Provides functionality to create a new chat instance using the specified
    serializer and ensures only authenticated users can perform the action.

    Attributes:
        queryset: The set of Chat objects available for operations. All
            instances of the Chat model are included.
        permission_classes: List containing the permission classes applied
            to this view. Only authenticated users are allowed.
        serializer_class: Specifies the serializer class to be used for
            serializing and deserializing chat data.
    """
    queryset = Chat.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = user_serializers.CreateChatSerializer


class EditChatView(generics.UpdateAPIView, GenericViewSet):
    """
    Handles updating information for a chat.

    This class-based view is used to update specific details of a chat instance.
    It is designed to ensure the user has the appropriate permissions and that the
    provided data is properly validated and serialized before updating the chat
    object. Inherits from Django REST framework's UpdateAPIView and additional
    viewset functionality.

    Attributes:
        queryset: The set of Chat instances from which the object to be updated
            is selected.
        permission_classes: A list of permission classes that check if the user
            has the necessary authorization. In this case, it ensures the user is
            an admin of the chat.
        serializer_class: Specifies the serializer used to validate and deserialize
            the incoming data before persisting changes to the Chat object.
    """
    queryset = Chat.objects.all()
    permission_classes = [
        c_prm.IsChatAdmin,
    ]
    serializer_class = user_serializers.UpdateChatSerializer


class ChatView(generics.RetrieveAPIView, GenericViewSet):
    """
    ChatView class retrieves chat details for a chat participant.

    This class extends RetrieveAPIView and GenericViewSet to provide a functionality
    for retrieving chat details. It ensures that only participants of the respective
    chat can access this information and returns chat data serialized in the format
    provided by the associated serializer. The class also includes error handling
    to return a standardized error message and HTTP status if an exception is encountered
    during the retrieval process.

    Attributes:
        queryset: Queryset for retrieving Chat objects.
        permission_classes: List of permissions required to access the resource.
        serializer_class: Serializer used for formatting the retrieved chat data.
    """
    queryset = Chat.objects.all()
    permission_classes = [c_prm.IsChatParticipant]
    serializer_class = user_serializers.ChatSerializer

    def get(self, request, *args, **kwargs):
        try:
            response = super().get(request, *args, **kwargs)
            return response.data

        except Exception as e:
            response_error_message = {"error": "An error occurred while retrieving the chat details"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatListView(generics.ListAPIView, GenericViewSet):
    """
    Represents a view for listing chats associated with the authenticated user.

    This class provides functionality to list all chats in which the user is a participant.
    It ensures that only authenticated users can access the chat data and uses a serializer
    to process the chat objects for the API response.

    Attributes:
        queryset: Represents the base queryset for fetching chat objects.
        permission_classes: Specifies the permissions required to access this view.
        serializer_class: Determines the serializer used to handle chat objects.

    Methods:
        get_queryset():
            Custom method to retrieve chats associated with the authenticated user.

    """
    queryset = Chat.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = user_serializers.ChatSerializer

    def get_queryset(self):
        headers = self.request.META.get("HTTP_AUTHORIZATION")
        token = headers.split("Bearer ")[1]
        user_id = CustomAuthToken.objects.get(key=token).user_id
        # Filter chats by participants through the related name 'participants'
        chat_ids = Participant.objects.filter(user_id=user_id).values_list("chat_id", flat=True)
        return Chat.objects.filter(id__in=chat_ids)


class GoogleLoginApi(APIView, TokenManager):
    """
    Handles Google login and authentication via OAuth2.

    This class integrates APIView for request handling and TokenManager for token
    management. It processes the Google OAuth2 login flow, validates incoming data,
    exchanges authorization codes for tokens, retrieves user information, and creates
    or updates user accounts in the application. The purpose of this class is to
    enable user authentication through their Google accounts and provide session
    tokens for authenticated users.
    """
    serializer_class = user_serializers.InputSerializer

    def get(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")
        input_serializer = self.serializer_class(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get("code")
        error = validated_data.get("error")
        state = validated_data.get("state")

        if error is not None:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        if code is None or state is None:
            return Response({"error": "Code and state are required."}, status=status.HTTP_400_BAD_REQUEST)

        session_state = request.session.get("google_oauth2_state")
        if session_state is None:
            return Response({"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST)

        del request.session["google_oauth2_state"]

        if state != session_state:
            return Response({"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST)

        google_login_flow = GoogleRawLoginFlowService()

        google_tokens = google_login_flow.get_tokens(code=code)

        id_token_decoded = google_tokens.decode_id_token()
        user_info = google_login_flow.get_user_info(google_tokens=google_tokens)

        user_email = id_token_decoded["email"]

        password = generate_user_password()

        user, created = CustomUser.objects.get_or_create(
            email=user_email,
            defaults={"username": id_token_decoded.get("name"), "google_id": id_token_decoded.get("sub")},
        )
        if user:
            user.google_id = id_token_decoded.get("sub")
            user.save()
        if created:
            user.set_password(password)
            CustomAuthToken.objects.create(user=user)
            user.save()

        if user is None:
            return Response({"error": f"User with email {user_email} is not found."}, status=status.HTTP_404_NOT_FOUND)

        login(request, user)

        token, created = self.get_or_create_token(user, user_agent)
        result = {"id_token_decoded": id_token_decoded, "user_info": user_info, "token": token.key}

        return Response(
            result,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
