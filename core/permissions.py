from rest_framework import permissions


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
