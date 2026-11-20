from django.contrib import admin

from .models import Application, Job, JobAlertLog, SavedJob


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "source", "job_type", "work_mode", "is_active", "created_at")
    list_filter = ("source", "job_type", "work_mode", "is_active")
    search_fields = ("title", "company", "location")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "seeker", "match_score", "status", "created_at")
    list_filter = ("status",)


admin.site.register(SavedJob)
admin.site.register(JobAlertLog)
