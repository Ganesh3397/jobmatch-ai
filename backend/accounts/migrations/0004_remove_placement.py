"""Remove the College Placement Cell (TPO) module.

* drops the old placement tables if they exist (the app was removed)
* turns any placement-officer accounts into normal job seekers
* removes the academic profile fields that only the placement module used
"""
from django.db import migrations, models

PLACEMENT_TABLES = ["placement_driveapplication", "placement_placementdrive"]


def drop_placement(apps, schema_editor):
    conn = schema_editor.connection
    existing = set(conn.introspection.table_names())
    with conn.cursor() as cur:
        for table in PLACEMENT_TABLES:
            if table in existing:
                cascade = " CASCADE" if conn.vendor == "postgresql" else ""
                cur.execute(f"DROP TABLE {schema_editor.quote_name(table)}{cascade}")
        if "django_migrations" in existing:
            cur.execute("DELETE FROM django_migrations WHERE app = %s", ["placement"])
        if "django_content_type" in existing:
            cur.execute("SELECT id FROM django_content_type WHERE app_label = %s", ["placement"])
            ids = [r[0] for r in cur.fetchall()]
            if ids:
                marks = ",".join(["%s"] * len(ids))
                if "auth_permission" in existing:
                    cur.execute(f"DELETE FROM auth_permission WHERE content_type_id IN ({marks})", ids)
                if "django_admin_log" in existing:
                    cur.execute(f"DELETE FROM django_admin_log WHERE content_type_id IN ({marks})", ids)
                cur.execute(f"DELETE FROM django_content_type WHERE id IN ({marks})", ids)

    User = apps.get_model("accounts", "User")
    User.objects.filter(role="tpo").update(role="seeker")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_demo_academic_profile")]

    operations = [
        migrations.RunPython(drop_placement, migrations.RunPython.noop),
        migrations.RemoveField(model_name="user", name="college"),
        migrations.RemoveField(model_name="user", name="branch"),
        migrations.RemoveField(model_name="user", name="graduation_year"),
        migrations.RemoveField(model_name="user", name="cgpa"),
        migrations.RemoveField(model_name="user", name="enrollment_no"),
        migrations.AlterField(
            model_name="user", name="role",
            field=models.CharField(choices=[("seeker", "Job Seeker"), ("recruiter", "Recruiter"), ("admin", "Admin")],
                                   default="seeker", max_length=20),
        ),
    ]
