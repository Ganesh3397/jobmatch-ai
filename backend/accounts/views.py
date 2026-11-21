import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import email_provider, send_email, sender_address
from .models import PasswordResetCode
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


MAX_CODE_ATTEMPTS = 5


def _reset_email(user, code, minutes):
    name = user.first_name or user.username
    text = (f"Hi {name},\n\nYour JobMatch AI password reset code is:\n\n    {code}\n\n"
            f"It is valid for {minutes} minutes. Enter it on the 'Forgot password' page to choose a new password.\n"
            "If you did not ask for this, you can ignore this email. Your password will not change.\n\n- JobMatch AI")
    digits = "".join(f'<span style="display:inline-block;width:38px;height:46px;line-height:46px;margin:0 3px;'
                     f'border-radius:10px;background:#eef0ff;color:#3b3bd6;font-size:24px;font-weight:800">{d}</span>'
                     for d in code)
    html = f"""<div style="font-family:Segoe UI,Arial,sans-serif;max-width:480px;margin:auto;padding:24px;color:#1b1f33">
  <div style="font-size:20px;font-weight:800;margin-bottom:6px">🔐 JobMatch AI</div>
  <p>Hi {name},</p>
  <p>Use this code to reset your password:</p>
  <div style="text-align:center;margin:22px 0">{digits}</div>
  <p style="color:#6b7190;font-size:13px">The code is valid for {minutes} minutes. If you did not ask for this,
  ignore this email. Your password will not change.</p>
</div>"""
    return text, html


class PasswordResetRequestView(APIView):
    """POST {email} -> emails a 6-digit reset code (valid for 10 minutes)."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response({"email": ["Please enter your email."]}, status=400)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({"email": ["No account is registered with this email."]}, status=404)
        if not user.is_active:
            return Response({"detail": "This account is disabled. Please contact the admin."}, status=403)
        if user.username in DEMO_USERNAMES:
            return Response({"detail": "The shared demo account's password cannot be reset."}, status=403)

        now = timezone.now()
        last = user.reset_codes.first()
        if last and (now - last.created_at).total_seconds() < 60:
            wait = 60 - int((now - last.created_at).total_seconds())
            return Response({"detail": f"Please wait {wait} seconds before asking for a new code.", "wait": wait},
                            status=429)
        if user.reset_codes.filter(created_at__gte=now - timedelta(hours=1)).count() >= 5:
            return Response({"detail": "Too many codes requested. Please try again after an hour."}, status=429)

        provider = email_provider()
        if not provider and not settings.DEBUG:
            return Response({"detail": "Password reset by email is not available yet because the site's email "
                                       "service is not set up. Please contact the admin to reset your password.",
                             "code": "email_not_configured"}, status=503)

        minutes = settings.PASSWORD_RESET_CODE_MINUTES
        code = f"{secrets.randbelow(10 ** 6):06d}"
        user.reset_codes.filter(used=False).update(used=True)  # only the newest code works
        rc = PasswordResetCode.objects.create(user=user, code_hash=make_password(code),
                                              expires_at=now + timedelta(minutes=minutes))
        text, html = _reset_email(user, code, minutes)
        ok, err = send_email(user.email, f"{code} is your JobMatch AI password reset code", text, html)

        masked = _mask(user.email)
        if ok:
            return Response({"detail": f"We sent a 6-digit code to {masked}.", "email": masked, "minutes": minutes})
        if not provider:  # DEBUG on a laptop without email set up: show the code so the flow can be tested
            return Response({"detail": "Email is not set up on this computer, so (development mode only) the code "
                                       "is shown here and printed in the backend terminal.",
                             "email": masked, "minutes": minutes, "dev_code": code})
        rc.delete()
        return Response({"detail": "We could not send the email right now. Please try again in a few minutes "
                                   "or contact the admin.", "code": "email_failed"}, status=502)


def _mask(email):
    name, _, domain = email.partition("@")
    shown = name[:2] if len(name) > 2 else name[:1]
    return f"{shown}{'*' * max(len(name) - len(shown), 1)}@{domain}"


def _check_code(user, code):
    """Returns (PasswordResetCode or None, error message)."""
    rc = user.reset_codes.filter(used=False).first() if user else None
    if not rc or rc.expires_at < timezone.now():
        return None, "This code has expired. Please request a new one."
    if rc.attempts >= MAX_CODE_ATTEMPTS:
        return None, "Too many wrong attempts. Please request a new code."
    if not check_password(str(code).strip(), rc.code_hash):
        rc.attempts += 1
        rc.save(update_fields=["attempts"])
        left = MAX_CODE_ATTEMPTS - rc.attempts
        return None, f"Wrong code. {left} attempt{'s' if left != 1 else ''} left." if left else \
            "Too many wrong attempts. Please request a new code."
    return rc, ""


class PasswordResetVerifyView(APIView):
    """POST {email, code} -> checks the code (lets the page move to the 'new password' step)."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        user = User.objects.filter(email__iexact=(request.data.get("email") or "").strip()).first()
        rc, err = _check_code(user, request.data.get("code", ""))
        if not rc:
            return Response({"code": [err]}, status=400)
        return Response({"detail": "Code verified."})


class PasswordResetConfirmView(APIView):
    """POST {email, code, new_password}"""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        user = User.objects.filter(email__iexact=(request.data.get("email") or "").strip()).first()
        rc, err = _check_code(user, request.data.get("code", ""))
        if not rc:
            return Response({"code": [err]}, status=400)
        pw = request.data.get("new_password", "")
        try:
            validate_password(pw, user)
        except DjangoValidationError as e:
            return Response({"new_password": e.messages}, status=400)
        user.set_password(pw)
        user.save()
        rc.used = True
        rc.save(update_fields=["used"])
        name = user.first_name or user.username
        send_email(user.email, "Your JobMatch AI password was changed",
                   f"Hi {name},\n\nYour JobMatch AI password was just changed. If this wasn't you, "
                   "reset it again right away and contact the admin.\n\n- JobMatch AI")
        return Response({"detail": "Password changed. You can now log in with your new password."})


class EmailStatusView(APIView):
    """Admin: which email provider is active."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        p = email_provider()
        return Response({"configured": bool(p), "provider": p, "sender": sender_address() if p else "",
                         "debug": settings.DEBUG})


class EmailTestView(APIView):
    """Admin: POST {to} -> sends a test email and returns the exact error if it fails."""
    permission_classes = [IsAdminRole]

    def post(self, request):
        to = (request.data.get("to") or request.user.email or "").strip()
        if not to:
            return Response({"detail": "Enter an email address."}, status=400)
        if not email_provider():
            return Response({"ok": False, "detail": "No email provider is configured. Add a Gmail App Password "
                                                     "(laptop) or BREVO_API_KEY (Render) in the environment."},
                            status=400)
        ok, err = send_email(to, "JobMatch AI test email ✅",
                             "Great news! Email sending from JobMatch AI works. Forgot-password codes will reach users.")
        if ok:
            return Response({"ok": True, "detail": f"Test email sent to {to}. Check the inbox (and spam)."})
        return Response({"ok": False, "detail": err}, status=502)


class UserAdminSetPasswordView(APIView):
    """Admin: set a new password for any user (fallback when email is not configured)."""
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        user = generics.get_object_or_404(User, pk=pk)
        pw = request.data.get("password", "")
        try:
            validate_password(pw, user)
        except DjangoValidationError as e:
            return Response({"password": e.messages}, status=400)
        user.set_password(pw)
        user.save()
        return Response({"detail": f"Password updated for {user.username}."})
