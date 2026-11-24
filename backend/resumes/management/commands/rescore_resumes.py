"""
Re-score resumes that were analysed with the old ATS rules.

Uses the text already saved in the database (no file needed), so it is fast.
Runs on every deploy from start.sh, but only touches resumes scored with an older
RULES_VERSION - so after the first run it does nothing until the rules change again.

    python manage.py rescore_resumes          # only old ones
    python manage.py rescore_resumes --all    # every resume
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from resumes.ml.analyzer import RULES_VERSION, analyze_resume
from resumes.ml.parser import parse_resume_text
from resumes.ml.roles import predict_roles
from resumes.ml.skill_extractor import extract_skills
from resumes.models import Resume


class Command(BaseCommand):
    help = "Re-calculate ATS score, skills and roles of resumes analysed with the old rules"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="re-score every resume")

    def handle(self, *args, **opts):
        qs = Resume.objects.filter(status=Resume.Status.DONE).exclude(raw_text="")
        done = 0
        for r in qs.iterator():
            if not opts["all"] and (r.analysis or {}).get("rules_version") == RULES_VERSION:
                continue
            parsed = parse_resume_text(r.raw_text)
            sk = extract_skills(parsed["text"], parsed["sections"].get("skills", ""))
            analysis = analyze_resume(parsed, sk["skills"])
            r.skills = sk["skills"]
            r.skills_by_category = sk["by_category"]
            r.ats_score = analysis["score"]
            r.analysis = analysis
            r.predicted_roles = predict_roles(sk["skills"], text=parsed["text"])
            r.processed_at = timezone.now()
            r.save(update_fields=["skills", "skills_by_category", "ats_score", "analysis", "predicted_roles", "processed_at"])
            done += 1
        self.stdout.write(self.style.SUCCESS(f"Re-scored {done} resume(s)"))
