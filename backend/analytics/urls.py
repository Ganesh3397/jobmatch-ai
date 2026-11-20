from django.urls import path

from . import views

urlpatterns = [
    path("seeker/", views.SeekerDashboardView.as_view()),
    path("recruiter/", views.RecruiterDashboardView.as_view()),
    path("admin/", views.AdminDashboardView.as_view()),
    path("market/", views.MarketInsightsView.as_view()),
]
