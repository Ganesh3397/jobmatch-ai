from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("change-password/", views.ChangePasswordView.as_view()),
    path("password-reset/", views.PasswordResetRequestView.as_view()),
    path("password-reset/verify/", views.PasswordResetVerifyView.as_view()),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view()),
    path("email/status/", views.EmailStatusView.as_view()),
    path("email/test/", views.EmailTestView.as_view()),
    path("users/", views.UserAdminListView.as_view()),
    path("users/create/", views.UserAdminCreateView.as_view()),
    path("users/<int:pk>/toggle/", views.UserAdminToggleView.as_view()),
    path("users/<int:pk>/set-password/", views.UserAdminSetPasswordView.as_view()),
]
