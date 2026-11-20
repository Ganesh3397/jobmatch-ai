from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "role", "phone",
            "location", "headline", "company_name", "job_alerts_enabled", "date_joined", "is_active",
        ]
        read_only_fields = ["id", "role", "date_joined", "is_active"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(
        choices=[User.Role.SEEKER, User.Role.RECRUITER], default=User.Role.SEEKER
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "role",
                  "phone", "location", "company_name"]

    def validate(self, attrs):
        if attrs.get("role") == User.Role.RECRUITER and not attrs.get("company_name"):
            raise serializers.ValidationError({"company_name": "Company name is required for recruiters."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class LoginSerializer(TokenObtainPairSerializer):
    """Login with username OR email, and return user details with the tokens."""

    def validate(self, attrs):
        login = attrs.get("username", "")
        if "@" in login:
            user = User.objects.filter(email__iexact=login).first()
            if user:
                attrs["username"] = user.username
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
