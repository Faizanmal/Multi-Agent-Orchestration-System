from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import APIKey, CustomUser, TwoFactorAuth, UserSession


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [  # noqa: RUF012
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'avatar', 'role', 'subscription_tier', 'is_2fa_enabled',
            'phone_number', 'user_timezone', 'profile_image', 'date_of_birth',
            'bio', 'location', 'website', 'email_notifications',
            'push_notifications', 'marketing_emails', 'theme_preference',
            'language', 'is_active', 'date_joined', 'last_activity'
        ]
        read_only_fields = ['id', 'date_joined', 'last_activity']  # noqa: RUF012
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            validate_password(password)
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [  # noqa: RUF012
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        attrs.pop('password_confirm')
        return attrs
    
    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password')
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Must provide email and password')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API keys"""
    key = serializers.CharField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = [  # noqa: RUF012
            'id', 'name', 'key', 'permissions', 'rate_limit',
            'usage_count', 'last_used', 'is_active', 'expires_at',
            'created_at'
        ]
        read_only_fields = ['id', 'key', 'usage_count', 'last_used', 'created_at']  # noqa: RUF012


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    class Meta:
        model = UserSession
        fields = [  # noqa: RUF012
            'id', 'session_key', 'ip_address', 'user_agent',
            'device_info', 'location', 'is_active',
            'last_activity', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity']  # noqa: RUF012


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    """Serializer for 2FA settings"""
    class Meta:
        model = TwoFactorAuth
        fields = [  # noqa: RUF012
            'is_enabled', 'last_used', 'created_at'
        ]
        read_only_fields = ['last_used', 'created_at']  # noqa: RUF012


class Enable2FASerializer(serializers.Serializer):
    """Serializer for enabling 2FA"""
    # Will be handled in view


class Verify2FASerializer(serializers.Serializer):
    """Serializer for verifying 2FA code"""
    code = serializers.CharField(max_length=6, min_length=6)