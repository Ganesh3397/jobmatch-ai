"""Business logic for processing a resume with the AI pipeline."""
import logging

from django.conf import settings
from django.utils import timezone

from .ml.analyzer import analyze_resume
from .ml.parser import extract_text, extract_text_from_bytes, parse_resume_text
from .ml.roles import predict_roles
from .ml.skill_extractor import extract_skills
from .models import Resume

log = logging.getLogger(__name__)


def process_resume(resume: Resume) -> Resume:
    resume.status = Resume.Status.PROCESSING
    resume.save(update_fields=["status"])
    try:
        try:
            raw = extract_text(resume.file.path)
        except Exception:  # file missing on disk (cloud restart) -> use DB copy
            if not resume.file_data:
                raise
            raw = extract_text_from_bytes(bytes(resume.file_data), resume.original_name)
        if len(raw.strip()) < 50:
            raise ValueError("Could not read text from this file. If it is a scanned image PDF, "
                             "please upload a text-based PDF or DOCX.")
        parsed = parse_resume_text(raw)
        sk = extract_skills(parsed["text"], parsed["sections"].get("skills", ""))
        analysis = analyze_resume(parsed, sk["skills"])

        resume.raw_text = parsed["text"]
        resume.candidate_name = parsed["name"]
        resume.email = parsed["email"]
        resume.phone = parsed["phone"]
        resume.links = parsed["links"]
        resume.skills = sk["skills"]
        resume.skills_by_category = sk["by_category"]
        resume.education = parsed["education"]
        resume.experience_years = parsed["experience_years"]
        resume.sections_found = [s for s in parsed["sections"] if s != "header"]
        resume.ats_score = analysis["score"]
        resume.analysis = analysis
        resume.predicted_roles = predict_roles(sk["skills"], text=parsed["text"])
        resume.status = Resume.Status.DONE
        resume.error = ""
        resume.processed_at = timezone.now()
        resume.save()
    except Exception as e:
        log.exception("Resume processing failed")
        resume.status = Resume.Status.FAILED
        resume.error = str(e)[:500]
        resume.save(update_fields=["status", "error"])
    return resume


def queue_resume_processing(resume: Resume):
    """Use Celery (background) when enabled, else process right away."""
    if getattr(settings, "ASYNC_PROCESSING", False):
        try:
            from .tasks import process_resume_task
            process_resume_task.delay(resume.id)
            return
        except Exception as e:  # broker not reachable
            log.warning("Celery unavailable (%s) - processing synchronously", e)
    process_resume(resume)


def get_primary_resume(user):
    qs = Resume.objects.filter(user=user, status=Resume.Status.DONE)
    return qs.filter(is_primary=True).first() or qs.first()
