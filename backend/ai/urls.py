from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.AIStatusView.as_view()),
    path("interviews/", views.InterviewListCreateView.as_view()),
    path("interviews/<int:pk>/", views.InterviewDetailView.as_view()),
    path("interviews/<int:pk>/answer/", views.InterviewAnswerView.as_view()),
    path("improve-resume/", views.ResumeImproverView.as_view()),
    path("cover-letters/", views.CoverLetterView.as_view()),
]
