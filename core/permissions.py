from django.db.models import Q
from rest_framework import permissions

from users.models import Team, Participant


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access only to order owner or admin
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        return obj.owner == request.user


class IsAdminOrStaff(permissions.BasePermission):
    """
    Allow access only to admin and staff users like managers
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user and (request.user.is_staff or request.user.is_admin))


class IsTeamMemberOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow only team members or the team leader to view team information.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_team_exist = Team.objects.filter(Q(list_of_members=request.user) | Q(leader=request.user)).exists()
        return bool(request.user and (request.user.is_staff or request.user.is_admin or user_team_exist))


class IsChatParticipant(permissions.BasePermission):
    """
    Custom permission to allow only chat participants.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        chat_id = view.kwargs.get('pk')
        if Participant.objects.filter(user=request.user, chat_id=chat_id).exists():
            return True



class IsChatAdmin(permissions.BasePermission):
    """
    Custom permission to allow only chat admins.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        chat_id = view.kwargs.get('pk')
        if chat_id and Participant.objects.filter(
                Q(user=request.user) & Q(chat_id=chat_id) & Q(role="admin")
        ).exists():
            return True

        return False