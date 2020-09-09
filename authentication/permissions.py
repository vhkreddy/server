from rest_framework import permissions
from .models import User


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, viewclass):
        if viewclass.action == 'list':
            return request.user.is_superuser
        else:
            return True


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.email == view.request.user.email
