"""Celery background tasks (run by `celery -A config worker` + `celery -A config beat`)."""
import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

log = logging.getLogger(__name__)


@shared_task
def fetch_jobs_for_resume(resume_id):
    from resumes.models import Resume

    from .services.recommender import default_query_for, fetch_live_jobs
    r = Resume.objects.filter(id=resume_id, status="done").first()
    if r:
        ids, _ = fetch_live_jobs(default_query_for(r), r.user.location or "")
        return len(ids)
    return 0


@shared_task
def refresh_live_jobs():
    """Every 6h: refresh live jobs for every distinct role users are interested in."""
    from resumes.models import Resume

    from .services.recommender import default_query_for, fetch_live_jobs
    queries = set()
    for r in Resume.objects.filter(status="done", is_primary=True).select_related("user"):
        queries.add((default_query_for(r), r.user.location or ""))
    total = 0
    for q, loc in queries:
        ids, _ = fetch_live_jobs(q, loc, force=True)
        total += len(ids)
    log.info("Refreshed %s live jobs for %s queries", total, len(queries))
    return total


@shared_task
def send_job_alerts(min_score=60, max_jobs=5):
    """Daily: email each seeker their top NEW matching jobs."""
    from resumes.services import get_primary_resume

    from .models import JobAlertLog
    from .services.recommender import recommend_jobs

    User = get_user_model()
    sent = 0
    for user in User.objects.filter(role="seeker", job_alerts_enabled=True, is_active=True).exclude(email=""):
        resume = get_primary_resume(user)
        if not resume:
            continue
        results, _ = recommend_jobs(resume, location=user.location or "", min_score=min_score, limit=40)
        already = set(JobAlertLog.objects.filter(user=user).values_list("job_id", flat=True))
        fresh = [r for r in results if r["job"].id not in already][:max_jobs]
        if not fresh:
            continue
        lines = [f"Hi {user.first_name or user.username},", "",
                 "New jobs matching your profile:", ""]
        for r in fresh:
            j, m = r["job"], r["match"]
            lines.append(f"• {j.title} — {j.company} ({j.location}) | Match {m['score']}%")
            if j.apply_url:
                lines.append(f"  Apply: {j.apply_url}")
        lines += ["", "— JobMatch AI"]
        send_mail(f"{len(fresh)} new jobs match your resume", "\n".join(lines),
                  settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        JobAlertLog.objects.bulk_create(
            [JobAlertLog(user=user, job=r["job"], score=r["match"]["score"]) for r in fresh],
            ignore_conflicts=True)
        sent += 1
    return sent
