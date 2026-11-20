from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("", views.ResumeViewSet, basename="resume")

urlpatterns = [
    path("match-jd/", views.JDMatchView.as_view()),
    path("match-history/", views.JDMatchHistoryView.as_view()),
    path("file/<str:token>/", views.ResumeFileView.as_view(), name="resume-file"),
] + router.urls
