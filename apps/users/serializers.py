from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType
from .models import User, UserFavorites, AuditLog

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'department', 'phone', 'avatar', 'preferences',
            'is_active', 'date_joined', 'last_login', 'password'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return data


class UserFavoritesSerializer(serializers.ModelSerializer):
    content_type_name = serializers.SerializerMethodField()
    object_str = serializers.SerializerMethodField()

    class Meta:
        model = UserFavorites
        fields = ['id', 'content_type', 'content_type_name', 'object_id', 'object_str', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_content_type_name(self, obj):
        return obj.content_type.model

    def get_object_str(self, obj):
        return str(obj.content_object) if obj.content_object else None


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'action', 'content_type', 'content_type_name', 
                  'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp']
        read_only_fields = ['id', 'timestamp']

    def get_content_type_name(self, obj):
        return obj.content_type.model

