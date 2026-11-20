from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import IsAdminRole
from .serializers import (AdminCreateUserSerializer, ChangePasswordSerializer,
                          LoginSerializer, RegisterSerializer, UserSerializer)

# Shared demo accounts: anyone can log in, nobody can lock others out
DEMO_USERNAMES = {"student", "demo_seeker0", "demo_seeker1", "demo_seeker2"}

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {"user": UserSerializer(user).data,
             "access": str(refresh.access_token),
             "refresh": str(refresh)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        if request.user.username in DEMO_USERNAMES:
            return Response({"detail": "This is a shared demo account. Please register your own account to edit a profile."},
                            status=403)
        return super().update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    def post(self, request):
        if request.user.username in DEMO_USERNAMES:
            return Response({"detail": "The demo account password cannot be changed."}, status=403)
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if not request.user.check_password(s.validated_data["old_password"]):
            return Response({"old_password": "Wrong password."}, status=400)
        request.user.set_password(s.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password changed successfully."})


class UserAdminListView(generics.ListAPIView):
    """Admin: list all users (with search & role filter)."""
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    queryset = User.objects.all().order_by("-date_joined")
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]


class UserAdminCreateView(generics.CreateAPIView):
    """Admin: create recruiter accounts (public sign-up only creates job seekers)."""
    serializer_class = AdminCreateUserSerializer
    permission_classes = [IsAdminRole]

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserAdminToggleView(APIView):
    """Admin: activate / deactivate a user."""
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        user = generics.get_object_or_404(User, pk=pk)
        if user == request.user:
            return Response({"detail": "You cannot deactivate yourself."}, status=400)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        return Response({"id": user.id, "is_active": user.is_active})
