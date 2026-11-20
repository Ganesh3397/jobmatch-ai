import os

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


def resume_upload_path(instance, filename):
    return f"resumes/user_{instance.user_id}/{filename}"


class Resume(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(["pdf", "docx", "txt"])],
    )
    original_name = models.CharField(max_length=255, blank=True)
    # copy of the file in PostgreSQL -> survives server restarts on cloud hosting
    file_data = models.BinaryField(null=True, blank=True, editable=False)
    content_type = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)

    # ---- AI output
    raw_text = models.TextField(blank=True)
    candidate_name = models.CharField(max_length=150, blank=True)
    email = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    links = models.JSONField(default=dict, blank=True)
    skills = models.JSONField(default=list, blank=True)
    skills_by_category = models.JSONField(default=dict, blank=True)
    education = models.JSONField(default=list, blank=True)
    experience_years = models.FloatField(default=0)
    sections_found = models.JSONField(default=list, blank=True)
    ats_score = models.PositiveIntegerField(default=0)
    analysis = models.JSONField(default=dict, blank=True)
    predicted_roles = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.original_name}"

    @property
    def top_role(self):
        return self.predicted_roles[0]["role"] if self.predicted_roles else ""

    def signed_file_url(self, request=None):
        """Temporary (7 day) link to download the resume, safe to open in a new tab."""
        from django.core import signing
        from django.urls import reverse
        url = reverse("resume-file", args=[signing.dumps(self.id, salt="resume-file")])
        return request.build_absolute_uri(url) if request else url

    def delete(self, *args, **kwargs):
        try:
            path = self.file.path if self.file else None
        except Exception:
            path = None
        super().delete(*args, **kwargs)
        if path and os.path.exists(path):
            os.remove(path)


class JDMatch(models.Model):
    """A seeker checking their resume against a pasted job description."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jd_matches")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="jd_matches")
    job_title = models.CharField(max_length=200, blank=True)
    job_description = models.TextField()
    score = models.FloatField(default=0)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
