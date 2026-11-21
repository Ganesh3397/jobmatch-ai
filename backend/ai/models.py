from django.conf import settings
from django.db import models


class InterviewSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interviews")
    role = models.CharField(max_length=150)
    job = models.ForeignKey("jobs.Job", null=True, blank=True, on_delete=models.SET_NULL)
    questions = models.JSONField(default=list)   # [{question, type, skill, points}]
    answers = models.JSONField(default=dict)     # {"0": {"answer": "...", "result": {...}}}
    overall_score = models.FloatField(null=True, blank=True)
    engine = models.CharField(max_length=80, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class CoverLetter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cover_letters")
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    tone = models.CharField(max_length=20, default="professional")
    letter = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
