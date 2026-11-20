from django.conf import settings
from rest_framework import serializers

from .models import JDMatch, Resume


class ResumeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ["id", "original_name", "is_primary", "status", "ats_score",
                  "experience_years", "created_at", "candidate_name"]


class ResumeDetailSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        exclude = ["raw_text", "user", "file", "file_data"]

    def get_file_url(self, obj):
        return obj.signed_file_url(self.context.get("request"))


class ResumeUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ["id", "file"]

    def validate_file(self, f):
        if f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise serializers.ValidationError(f"File too large. Max {settings.MAX_UPLOAD_MB} MB.")
        return f


class JDMatchRequestSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField(required=False)
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    job_description = serializers.CharField(min_length=30)


class JDMatchSerializer(serializers.ModelSerializer):
    resume_name = serializers.CharField(source="resume.original_name", read_only=True)

    class Meta:
        model = JDMatch
        fields = ["id", "resume", "resume_name", "job_title", "score", "result", "created_at"]
