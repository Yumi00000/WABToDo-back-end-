from rest_framework import permissions


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        if hasattr(obj, "owner") and obj.owner == request.user:
            return True

        return False
