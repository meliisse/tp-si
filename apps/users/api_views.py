from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from .models import User, UserFavorites, AuditLog
from .serializers import UserSerializer, LoginSerializer, UserFavoritesSerializer, AuditLogSerializer

class IsAdminOrSelf(permissions.BasePermission):
    """
    Custom permission to only allow admins or the user themselves to access/modify
    """
    def has_object_permission(self, request, view, obj):
        # Allow admins to do anything
        if request.user.role == 'admin':
            return True
        # Allow users to access/modify their own profile
        return obj == request.user

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'date_joined', 'role']
    ordering = ['-date_joined']

    def get_permissions(self):
        """
        Override to allow user registration without authentication
        """
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        """
        Filter queryset based on user role
        """
        queryset = User.objects.all()
        user = self.request.user

        if user.role == 'agent':
            # Agents can only see other agents and themselves
            return queryset.filter(role__in=['agent', 'chauffeur']) | queryset.filter(id=user.id)
        elif user.role == 'chauffeur':
            # Chauffeurs can only see themselves
            return queryset.filter(id=user.id)

        return queryset

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Custom login endpoint that returns JWT tokens"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)
            if user:
                # Log successful login
                LoginHistory.objects.create(
                    user=user,
                    username_attempted=username,
                    status='success',
                    ip_address=getattr(request, '_audit_ip', None),
                    user_agent=getattr(request, '_audit_user_agent', '')
                )
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            else:
                # Log failed login
                LoginHistory.objects.create(
                    user=None,
                    username_attempted=username,
                    status='failed',
                    ip_address=getattr(request, '_audit_ip', None),
                    user_agent=getattr(request, '_audit_user_agent', '')
                )
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Allow users to change their password"""
        user = self.get_object()

        # Check permissions
        if not (request.user == user or request.user.role == 'admin'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Admin only: Activate/deactivate user"""
        if request.user.role != 'admin':
            return Response({'error': 'Admin permission required'}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({'message': f'User {"activated" if user.is_active else "deactivated"}'})

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """Request password reset"""
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build reset URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

            # Send email
            subject = 'Password Reset Request'
            html_message = render_to_string('emails/password_reset.html', {
                'user': user,
                'reset_url': reset_url,
            })
            plain_message = f"""
            Hello {user.username},

            You have requested to reset your password. Click the link below to reset it:

            {reset_url}

            If you didn't request this, please ignore this email.

            Best regards,
            Transport Management System
            """

            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return Response({'message': 'Password reset email sent'})
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            return Response({'message': 'Password reset email sent'})
        except Exception as e:
            return Response({'error': 'Failed to send reset email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserFavoritesViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user favorites"""
    serializer_class = UserFavoritesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own favorites
        return UserFavorites.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def add_favorite(self, request):
        """Add an item to favorites"""
        content_type_id = request.data.get('content_type')
        object_id = request.data.get('object_id')
        
        if not content_type_id or not object_id:
            return Response({'error': 'content_type and object_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            content_type = ContentType.objects.get(id=content_type_id)
        except ContentType.DoesNotExist:
            return Response({'error': 'Invalid content_type'}, status=status.HTTP_400_BAD_REQUEST)
        
        favorite, created = UserFavorites.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        )
        
        if created:
            return Response(UserFavoritesSerializer(favorite).data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already in favorites'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def remove_favorite(self, request):
        """Remove an item from favorites"""
        content_type_id = request.data.get('content_type')
        object_id = request.data.get('object_id')
        
        if not content_type_id or not object_id:
            return Response({'error': 'content_type and object_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            favorite = UserFavorites.objects.get(
                user=request.user,
                content_type_id=content_type_id,
                object_id=object_id
            )
            favorite.delete()
            return Response({'message': 'Removed from favorites'}, status=status.HTTP_204_NO_CONTENT)
        except UserFavorites.DoesNotExist:
            return Response({'error': 'Not in favorites'}, status=status.HTTP_404_NOT_FOUND)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs (read-only)"""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user', 'action', 'content_type']
    search_fields = ['object_repr', 'user__username']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        # Admins can see all logs, others only their own
        if self.request.user.role == 'admin':
            return AuditLog.objects.all()
        return AuditLog.objects.filter(user=self.request.user)

