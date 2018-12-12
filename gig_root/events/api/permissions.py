from rest_framework import permissions


class IsOwnerEvent(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an event to edit the event.
    """

    def has_object_permission(self, request, view, event):
        if request.method in permissions.SAFE_METHODS:
            return True

        return event.is_owner(request.user)
