from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SEEKER = "seeker", "Job Seeker"
        RECRUITER = "recruiter", "Recruiter"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SEEKER)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=120, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    company_name = models.CharField(max_length=150, blank=True)  # recruiters
    job_alerts_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_seeker(self):
        return self.role == self.Role.SEEKER

    @property
    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
