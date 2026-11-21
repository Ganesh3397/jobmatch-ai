from django.contrib import admin

from .models import CoverLetter, InterviewSession


@admin.register(InterviewSession)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "overall_score", "completed", "created_at")


admin.site.register(CoverLetter)
