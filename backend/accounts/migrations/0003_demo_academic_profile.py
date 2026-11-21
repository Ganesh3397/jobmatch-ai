"""Give the shared demo accounts academic details so they can try Campus Drives (profile is locked for them)."""
from django.db import migrations

DEMO = {
    "student": ("Savitribai Phule Pune University", "MCA", 2026, 8.4, "MCA2024-017"),
    "demo_seeker0": ("", "MCA", 2026, 7.9, "DEMO-001"),
    "demo_seeker1": ("", "BCA", 2026, 6.8, "DEMO-002"),
    "demo_seeker2": ("", "MCA", 2026, 8.8, "DEMO-003"),
}


def fill(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for username, (college, branch, year, cgpa, roll) in DEMO.items():
        u = User.objects.filter(username=username, branch="").first()
        if u:
            u.college = u.college or college
            u.branch, u.graduation_year, u.cgpa, u.enrollment_no = branch, year, cgpa, roll
            u.save(update_fields=["college", "branch", "graduation_year", "cgpa", "enrollment_no"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_branch_user_cgpa_user_college_and_more")]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
