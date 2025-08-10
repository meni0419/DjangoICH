from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Читать можно всем (с учётом глобальных пермишенов),
    изменять/удалять — только владельцу объекта.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, 'owner_id', None) == getattr(request.user, 'id', None)

