from rest_framework import serializers

from resumes.ml.skill_extractor import extract_skills

from .models import Application, Job, SavedJob


class JobSerializer(serializers.ModelSerializer):
    source_label = serializers.CharField(source="get_source_display", read_only=True)
    job_type_label = serializers.CharField(source="get_job_type_display", read_only=True)
    work_mode_label = serializers.CharField(source="get_work_mode_display", read_only=True)
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "source", "source_label", "title", "company", "location", "description", "skills",
            "job_type", "job_type_label", "work_mode", "work_mode_label", "min_experience",
            "salary_min", "salary_max", "apply_url", "is_active", "posted_at", "created_at",
            "applications_count",
        ]
        read_only_fields = ["source", "posted_at", "created_at"]

    def get_applications_count(self, obj):
        if obj.source != Job.Source.INTERNAL:
            return None
        n = getattr(obj, "n_apps", None)
        return n if n is not None else obj.applications.count()

    def validate(self, attrs):
        # auto-detect skills from the description if recruiter left them empty
        if not attrs.get("skills") and attrs.get("description"):
            attrs["skills"] = extract_skills(f"{attrs.get('title', '')}\n{attrs['description']}")["skills"][:20]
        return attrs


class JobLiteSerializer(serializers.ModelSerializer):
    source_label = serializers.CharField(source="get_source_display", read_only=True)
    job_type_label = serializers.CharField(source="get_job_type_display", read_only=True)
    work_mode_label = serializers.CharField(source="get_work_mode_display", read_only=True)
    short_description = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ["id", "source", "source_label", "title", "company", "location", "skills",
                  "job_type", "job_type_label", "work_mode", "work_mode_label", "min_experience",
                  "salary_min", "salary_max", "apply_url", "publisher", "posted_at", "created_at", "short_description"]

    def get_short_description(self, obj):
        d = " ".join(obj.description.split())
        return d[:260] + ("…" if len(d) > 260 else "")


class ApplicationSerializer(serializers.ModelSerializer):
    job = JobLiteSerializer(read_only=True)
    seeker_name = serializers.SerializerMethodField()
    seeker_email = serializers.EmailField(source="seeker.email", read_only=True)
    resume_url = serializers.SerializerMethodField()
    resume_skills = serializers.JSONField(source="resume.skills", read_only=True)
    resume_ats = serializers.IntegerField(source="resume.ats_score", read_only=True)
    experience_years = serializers.FloatField(source="resume.experience_years", read_only=True)

    class Meta:
        model = Application
        fields = ["id", "job", "seeker_name", "seeker_email", "resume_url", "resume_skills", "resume_ats",
                  "experience_years", "match_score", "match_result", "cover_note", "status",
                  "created_at", "updated_at"]
        read_only_fields = ["match_score", "match_result", "created_at", "updated_at"]

    def get_seeker_name(self, obj):
        return obj.seeker.get_full_name() or obj.seeker.username

    def get_resume_url(self, obj):
        return obj.resume.signed_file_url(self.context.get("request")) if obj.resume else ""


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobLiteSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(source="job", queryset=Job.objects.all(), write_only=True)

    class Meta:
        model = SavedJob
        fields = ["id", "job", "job_id", "status", "match_score", "notes", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
