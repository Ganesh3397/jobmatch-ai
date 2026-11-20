from collections import Counter
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole, IsRecruiter, IsSeeker
from jobs.models import Application, Job, SavedJob
from resumes.ml.skill_extractor import technical_only
from resumes.models import Resume
from resumes.services import get_primary_resume

User = get_user_model()


def skill_demand(limit_jobs=500, top=20):
    """Most demanded skills across stored jobs (cached 1h in Redis)."""
    key = f"analytics:skill_demand:{limit_jobs}:{top}"
    data = cache.get(key)
    if data is None:
        c = Counter()
        for skills in Job.objects.filter(is_active=True).order_by("-created_at") \
                .values_list("skills", flat=True)[:limit_jobs]:
            c.update(technical_only(skills or []))
        data = [{"skill": s, "count": n} for s, n in c.most_common(top)]
        cache.set(key, data, 60 * 60)
    return data


class SeekerDashboardView(APIView):
    permission_classes = [IsSeeker]

    def get(self, request):
        u = request.user
        resume = get_primary_resume(u)
        resumes = Resume.objects.filter(user=u, status="done").order_by("created_at")
        saved = dict(SavedJob.objects.filter(user=u).values_list("status").annotate(n=Count("id")))
        apps = Application.objects.filter(seeker=u)

        demand = skill_demand()
        have = {s.lower() for s in (resume.skills if resume else [])}
        lacking = [d for d in demand if d["skill"].lower() not in have][:8]

        return Response({
            "has_resume": bool(resume),
            "primary_resume": {
                "id": resume.id, "name": resume.original_name, "ats_score": resume.ats_score,
                "grade": resume.analysis.get("grade"), "skills_count": len(resume.skills),
                "experience_years": resume.experience_years, "predicted_roles": resume.predicted_roles,
                "skills_by_category": {k: len(v) for k, v in resume.skills_by_category.items()},
            } if resume else None,
            "ats_history": [{"name": r.original_name[:18], "score": r.ats_score,
                             "date": r.created_at.date().isoformat()} for r in resumes],
            "tracker": {s: saved.get(s, 0) for s in SavedJob.Status.values},
            "applications": apps.count(),
            "avg_application_match": round(apps.aggregate(a=Avg("match_score"))["a"] or 0, 1),
            "skills_in_demand_you_lack": lacking,
        })


class RecruiterDashboardView(APIView):
    permission_classes = [IsRecruiter]

    def get(self, request):
        jobs = Job.objects.filter(posted_by=request.user)
        apps = Application.objects.filter(job__posted_by=request.user)
        per_job = jobs.annotate(n=Count("applications"), avg=Avg("applications__match_score")) \
            .values("id", "title", "n", "avg").order_by("-n")[:10]
        return Response({
            "total_jobs": jobs.count(),
            "active_jobs": jobs.filter(is_active=True).count(),
            "total_applicants": apps.count(),
            "avg_match_score": round(apps.aggregate(a=Avg("match_score"))["a"] or 0, 1),
            "status_breakdown": {s: apps.filter(status=s).count() for s in Application.Status.values},
            "per_job": [{"id": j["id"], "title": j["title"], "applicants": j["n"],
                         "avg_match": round(j["avg"] or 0, 1)} for j in per_job],
            "top_candidates": [
                {"name": a.seeker.get_full_name() or a.seeker.username, "job": a.job.title,
                 "score": a.match_score, "status": a.status}
                for a in apps.select_related("seeker", "job").order_by("-match_score")[:5]
            ],
        })


class AdminDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        since = timezone.now() - timedelta(days=13)
        signups = User.objects.filter(date_joined__gte=since).annotate(d=TruncDate("date_joined")) \
            .values("d").annotate(n=Count("id"))
        signup_map = {str(x["d"]): x["n"] for x in signups}
        days = [(since + timedelta(days=i)).date().isoformat() for i in range(14)]

        supply = Counter()
        for skills in Resume.objects.filter(status="done").values_list("skills", flat=True)[:1000]:
            supply.update(technical_only(skills or []))

        done = Resume.objects.filter(status="done")
        return Response({
            "users": {r: User.objects.filter(role=r).count() for r in User.Role.values},
            "total_users": User.objects.count(),
            "resumes_processed": done.count(),
            "resumes_failed": Resume.objects.filter(status="failed").count(),
            "avg_ats_score": round(done.aggregate(a=Avg("ats_score"))["a"] or 0, 1),
            "jobs_by_source": {s: Job.objects.filter(source=s).count() for s in Job.Source.values},
            "total_jobs": Job.objects.count(),
            "applications_by_status": {s: Application.objects.filter(status=s).count()
                                       for s in Application.Status.values},
            "signups_14_days": [{"date": d, "count": signup_map.get(d, 0)} for d in days],
            "skill_demand": skill_demand(top=12),
            "skill_supply": [{"skill": s, "count": n} for s, n in supply.most_common(12)],
            "ats_distribution": [
                {"range": label, "count": done.filter(ats_score__gte=lo, ats_score__lte=hi).count()}
                for label, lo, hi in [("0-40", 0, 40), ("41-60", 41, 60), ("61-80", 61, 80), ("81-100", 81, 100)]
            ],
        })


class MarketInsightsView(APIView):
    """Any logged-in user: top skills employers want right now."""

    def get(self, request):
        return Response({"skill_demand": skill_demand(top=15),
                         "jobs_tracked": Job.objects.filter(is_active=True).count()})
