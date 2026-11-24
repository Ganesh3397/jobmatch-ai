from django.conf import settings
from django.db import models


class Job(models.Model):
    class Source(models.TextChoices):
        INTERNAL = "internal", "Posted on JobMatch"
        ADZUNA = "adzuna", "Adzuna"
        JSEARCH = "jsearch", "JSearch (LinkedIn/Indeed/Glassdoor)"
        REMOTIVE = "remotive", "Remotive"
        JOBICY = "jobicy", "Jobicy"
        ARBEITNOW = "arbeitnow", "Arbeitnow"
        GREENHOUSE = "greenhouse", "Company careers page"
        LEVER = "lever", "Company careers page"
        DEMO = "demo", "Demo data"

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        INTERNSHIP = "internship", "Internship"
        CONTRACT = "contract", "Contract"

    class WorkMode(models.TextChoices):
        ONSITE = "onsite", "On-site"
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"

    source = models.CharField(max_length=20, choices=Source.choices, default=Source.INTERNAL, db_index=True)
    external_id = models.CharField(max_length=200, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.ONSITE)
    min_experience = models.FloatField(default=0)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    apply_url = models.URLField(max_length=1000, blank=True)
    publisher = models.CharField(max_length=80, blank=True)  # original site, e.g. LinkedIn, Naukri.com, Indeed
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.CASCADE, related_name="posted_jobs")
    search_query = models.CharField(max_length=200, blank=True)  # which query fetched it
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["source", "external_id"],
                                    condition=~models.Q(external_id=""),
                                    name="uniq_external_job"),
        ]
        indexes = [models.Index(fields=["is_active", "source"])]

    def __str__(self):
        return f"{self.title} @ {self.company}"

    @property
    def text_for_matching(self):
        return f"{self.title}\n{' '.join(self.skills)}\n{self.description}"


class Application(models.Model):
    """Seeker applying to a job posted by a recruiter on this platform."""

    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INTERVIEW = "interview", "Interview"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    seeker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    resume = models.ForeignKey("resumes.Resume", on_delete=models.SET_NULL, null=True)
    match_score = models.FloatField(default=0)
    match_result = models.JSONField(default=dict)
    cover_note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-match_score"]
        unique_together = ("job", "seeker")


class SavedJob(models.Model):
    """Seeker's personal application tracker (works for live/external jobs too)."""

    class Status(models.TextChoices):
        SAVED = "saved", "Saved"
        APPLIED = "applied", "Applied"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SAVED)
    match_score = models.FloatField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ("user", "job")


class JobAlertLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
