from django.db.models import Q
from rest_framework import permissions

from users.models import Team, Participant, CustomAuthToken


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission class to check if a user is either the owner of an order or has admin privileges.

    This class extends the Django REST framework BasePermission to define a custom permission. It ensures
    that access is granted only if the requesting user is an admin (staff member) or is the owner of the
    specific object/order being accessed.
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        return obj.owner == request.user


class IsAdminOrStaff(permissions.BasePermission):
    """
    Permission class to check if a user is either a staff member or an admin.

    This permission class is used to grant access to certain views or functionalities
    to users who hold staff or admin roles. It determines user permissions based on
    their authentication status and roles.

    Attributes:
        None
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user and (request.user.is_staff or request.user.is_admin))


class IsTeamMemberOrAdmin(permissions.BasePermission):
    """
    A class that implements a custom permission to check if a user is a team member or has admin privileges.

    This permission class is used to verify if a user is either part of a team, the leader of a team,
    or has administrative access based on the request information. It helps to control access to
    specific views by restricting unauthorized users.

    Attributes:
        None
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_team_exist = Team.objects.filter(Q(list_of_members=request.user) | Q(leader=request.user)).exists()
        return bool(request.user and (request.user.is_staff or request.user.is_admin or user_team_exist))


class IsChatParticipant(permissions.BasePermission):
    """
    Custom permission class to check if a user is a participant in a specific chat.

    This class is designed to enforce permission rules where access to certain
    views is restricted to users who are authenticated and are participants
    of the chat that corresponds to a specific identifier (e.g., primary key)
    provided in the view's keyword arguments.

    Attributes:
        None
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        chat_id = view.kwargs.get("pk")
        if Participant.objects.filter(user=request.user, chat_id=chat_id).exists():
            return True


class IsChatAdmin(permissions.BasePermission):
    """
    Permission class for determining if a user is an administrator of a specific chat.

    This class is used to check if the currently authenticated user has the role
    of 'admin' in a chat specified by its ID (retrieved from the view's kwargs).
    If the user meets the condition, permission is granted; otherwise, it is denied.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        chat_id = view.kwargs.get("pk")
        if chat_id and Participant.objects.filter(Q(user=request.user) & Q(chat_id=chat_id) & Q(role="admin")).exists():
            return True

        return False


class IsAccountOwner(permissions.BasePermission):
    """
    Custom permission class to check if the requesting user is the owner of the account.

    This permission class ensures that the authenticated user matches the user associated
    with the provided token and the account ID in the request. It works by verifying the
    user's authentication status, extracting the authorization token from the header, and
    validating if the token belongs to the user specified in the request.

    Attributes:
        None

    Methods:
        None
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        header = request.META.get("HTTP_AUTHORIZATION")
        key = header.split()[1]

        if CustomAuthToken.objects.filter(key=key, user_id=view.kwargs.get("pk")).exists():
            return True

        return False
