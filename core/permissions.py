from rest_framework import permissions

from users.models import Team


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access only to order owner or admin
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        if hasattr(obj, "owner") and obj.owner == request.user:
            return True

        return False


class IsAdminOrStaff(permissions.BasePermission):
    """
    Allow access only to admin and staff users like managers
    """

    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_admin))


class IsTeamMemberOrLeader(permissions.BasePermission):
    """
    Custom permission to allow only team members or the team leader to view team information.
    """

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Team):
            return False

        if hasattr(obj, "leader") and obj.leader == request.user:
            return True

        return obj.list_of_members.filter(id=request.user.id).exists()
