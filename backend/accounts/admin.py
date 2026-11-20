from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "company_name", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "company_name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("role", "phone", "location", "headline",
                                "company_name", "job_alerts_enabled")}),
    )
