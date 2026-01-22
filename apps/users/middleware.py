"""
Middleware for automatic audit logging of all model changes
"""
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from apps.users.models import AuditLog


class AuditLogMiddleware(MiddlewareMixin):
    """Middleware to automatically log all database operations"""
    
    def process_request(self, request):
        # Store request info for later use in signals
        request._audit_ip = self.get_client_ip(request)
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def log_action(user, action, obj, changes=None, request=None):
    """
    Helper function to log an action
    
    Args:
        user: User who performed the action
        action: Action type ('create', 'update', 'delete', 'view', 'export')
        obj: The object that was affected
        changes: Dict of changes made (for updates)
        request: HTTP request object (optional)
    """
    if not (user and user.is_authenticated and obj):
        return

    # Ensure changes are JSON serializable (Decimal, datetime, etc.)
    serializable_changes = changes or {}
    try:
        serializable_changes = json.loads(json.dumps(serializable_changes, cls=DjangoJSONEncoder))
    except TypeError:
        serializable_changes = {"detail": str(serializable_changes)}

    content_type = ContentType.objects.get_for_model(obj)

    audit_data = {
        'user': user,
        'action': action,
        'content_type': content_type,
        'object_id': obj.pk,
        'object_repr': str(obj)[:200],
        'changes': serializable_changes,
    }
    
    if request:
        audit_data['ip_address'] = getattr(request, '_audit_ip', None)
        audit_data['user_agent'] = getattr(request, '_audit_user_agent', '')
    
    AuditLog.objects.create(**audit_data)
