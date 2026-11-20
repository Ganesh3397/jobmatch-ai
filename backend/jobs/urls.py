from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("saved", views.SavedJobViewSet, basename="saved-job")
router.register("", views.JobViewSet, basename="job")

urlpatterns = [
    path("live/", views.LiveJobsView.as_view(), name="live-jobs"),
    path("applications/mine/", views.MyApplicationsView.as_view()),
    path("applications/<int:pk>/", views.ApplicationStatusView.as_view()),
] + router.urls
