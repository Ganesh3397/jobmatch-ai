from django.contrib import admin

from .models import JDMatch, Resume, SkillProgress


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "original_name", "status", "ats_score", "experience_years", "is_primary", "created_at")
    list_filter = ("status", "is_primary")
    search_fields = ("user__username", "candidate_name", "original_name")
    readonly_fields = ("raw_text", "analysis", "skills", "skills_by_category", "predicted_roles")


@admin.register(JDMatch)
class JDMatchAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "job_title", "score", "created_at")


admin.site.register(SkillProgress)
