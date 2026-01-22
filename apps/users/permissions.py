from rest_framework import permissions


class IsAgent(permissions.BasePermission):
    """
    Permission pour les agents de transport
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['agent', 'admin']


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission pour les administrateurs ou lecture seule pour les autres
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == 'admin'


class CanCreateExpedition(permissions.BasePermission):
    """
    Permission pour créer des expéditions (agents et admins)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['agent', 'admin']


class CanModifyCriticalData(permissions.BasePermission):
    """
    Permission pour modifier des données critiques (admins seulement)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsChauffeurOrAdmin(permissions.BasePermission):
    """
    Permission pour les chauffeurs ou admins
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['chauffeur', 'admin']


class CanViewAnalytics(permissions.BasePermission):
    """
    Permission pour voir les analyses (agents et admins)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['agent', 'admin']


class CanManageUsers(permissions.BasePermission):
    """
    Permission pour gérer les utilisateurs (admins seulement)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class CanManageBilling(permissions.BasePermission):
    """
    Permission pour gérer la facturation (agents et admins)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['agent', 'admin']


class CanManageSupport(permissions.BasePermission):
    """
    Permission pour gérer le support (agents et admins)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['agent', 'admin']
