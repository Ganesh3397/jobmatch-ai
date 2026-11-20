from django.db.models import Count
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRecruiter, IsSeeker
from resumes.ml.matcher import match_label, match_one, matcher_backend_name
from resumes.services import get_primary_resume

from .models import Application, Job, SavedJob
from .serializers import (ApplicationSerializer, JobLiteSerializer,
                          JobSerializer, SavedJobSerializer)
from .services.recommender import recommend_jobs


class JobViewSet(viewsets.ModelViewSet):
    """
    Jobs posted on this platform by recruiters (+ browse all stored jobs).
    GET  /api/jobs/                 all active jobs (search, filter)
    GET  /api/jobs/mine/            recruiter: own jobs
    POST /api/jobs/                 recruiter: post a job
    POST /api/jobs/{id}/apply/      seeker: apply (AI match score saved)
    GET  /api/jobs/{id}/applicants/ recruiter: applicants ranked by AI score
    GET  /api/jobs/{id}/match/      seeker: my match for this job
    """
    serializer_class = JobSerializer
    filterset_fields = ["source", "job_type", "work_mode", "is_active"]
    search_fields = ["title", "company", "location", "description"]
    ordering_fields = ["created_at", "salary_max", "min_experience"]

    def get_queryset(self):
        qs = Job.objects.all()
        if self.action == "list":
            qs = qs.filter(is_active=True)
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "mine", "applicants"):
            return [IsRecruiter()]
        if self.action in ("apply", "match"):
            return [IsSeeker()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user, source=Job.Source.INTERNAL,
                        company=serializer.validated_data.get("company") or self.request.user.company_name)

    def _check_owner(self, job):
        u = self.request.user
        if job.posted_by_id != u.id and not u.is_admin_role:
            raise PermissionDenied("You can only manage your own job posts.")

    def perform_update(self, serializer):
        self._check_owner(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_owner(instance)
        instance.delete()

    @action(detail=False)
    def mine(self, request):
        qs = Job.objects.filter(posted_by=request.user).annotate(n_apps=Count("applications"))
        return Response(JobSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        job = self.get_object()
        if job.source != Job.Source.INTERNAL:
            raise ValidationError("This is an external job. Use the Apply link to apply on the company site.")
        resume = get_primary_resume(request.user)
        if not resume:
            raise ValidationError("Please upload your resume before applying.")
        if Application.objects.filter(job=job, seeker=request.user).exists():
            raise ValidationError("You have already applied to this job.")
        m = match_one(resume.raw_text, resume.skills, resume.experience_years,
                      job.text_for_matching, job.skills, job.min_experience)
        m["label"] = match_label(m["score"])
        app = Application.objects.create(job=job, seeker=request.user, resume=resume,
                                         match_score=m["score"], match_result=m,
                                         cover_note=request.data.get("cover_note", ""))
        SavedJob.objects.update_or_create(user=request.user, job=job,
                                          defaults={"status": SavedJob.Status.APPLIED, "match_score": m["score"]})
        return Response(ApplicationSerializer(app, context={"request": request}).data, status=201)

    @action(detail=True)
    def applicants(self, request, pk=None):
        job = self.get_object()
        self._check_owner(job)
        qs = job.applications.select_related("seeker", "resume").order_by("-match_score")
        st = request.query_params.get("status")
        if st:
            qs = qs.filter(status=st)
        return Response(ApplicationSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=True)
    def match(self, request, pk=None):
        job = self.get_object()
        resume = get_primary_resume(request.user)
        if not resume:
            raise ValidationError("Please upload your resume first.")
        m = match_one(resume.raw_text, resume.skills, resume.experience_years,
                      job.text_for_matching, job.skills, job.min_experience)
        m["label"] = match_label(m["score"])
        m["engine"] = matcher_backend_name()
        applied = Application.objects.filter(job=job, seeker=request.user).exists()
        return Response({"job": JobSerializer(job).data, "match": m, "applied": applied})


class LiveJobsView(APIView):
    """
    GET /api/jobs/live/?q=&location=&job_type=&work_mode=&min_score=&refresh=1
    Real-time jobs for the user's profile, ranked by AI match score.
    """
    permission_classes = [IsSeeker]

    def get(self, request):
        resume = get_primary_resume(request.user)
        if not resume:
            return Response({"detail": "Please upload your resume to get job recommendations."}, status=400)
        p = request.query_params
        try:
            min_score = float(p.get("min_score", 0) or 0)
        except ValueError:
            min_score = 0
        results, meta = recommend_jobs(
            resume, query=p.get("q", ""), location=p.get("location", ""),
            job_type=p.get("job_type", ""), work_mode=p.get("work_mode", ""),
            min_score=min_score, limit=int(p.get("limit", 30)),
            force_refresh=p.get("refresh") == "1",
        )
        saved = dict(SavedJob.objects.filter(user=request.user).values_list("job_id", "status"))
        applied = set(Application.objects.filter(seeker=request.user).values_list("job_id", flat=True))
        data = []
        for r in results:
            j = JobLiteSerializer(r["job"]).data
            j["saved_status"] = saved.get(r["job"].id)
            j["applied"] = r["job"].id in applied
            data.append({"job": j, "match": r["match"]})
        meta["engine"] = matcher_backend_name()
        meta["resume_id"] = resume.id
        meta["suggested_queries"] = [x["role"] for x in resume.predicted_roles]
        return Response({"meta": meta, "results": data})


class SavedJobViewSet(viewsets.ModelViewSet):
    """Personal job tracker: saved → applied → interview → offer / rejected."""
    permission_classes = [IsSeeker]
    serializer_class = SavedJobSerializer
    pagination_class = None
    filterset_fields = ["status"]

    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related("job")

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj, created = SavedJob.objects.update_or_create(
            user=request.user, job=s.validated_data["job"],
            defaults={k: v for k, v in s.validated_data.items() if k != "job"},
        )
        return Response(self.get_serializer(obj).data, status=201 if created else 200)


class MyApplicationsView(generics.ListAPIView):
    permission_classes = [IsSeeker]
    serializer_class = ApplicationSerializer
    pagination_class = None

    def get_queryset(self):
        return Application.objects.filter(seeker=self.request.user).select_related("job", "resume")


class ApplicationStatusView(mixins.UpdateModelMixin, generics.GenericAPIView):
    """Recruiter: PATCH /api/jobs/applications/{id}/  {"status": "shortlisted"}"""
    permission_classes = [IsRecruiter]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        u = self.request.user
        qs = Application.objects.select_related("job", "seeker", "resume")
        return qs if u.is_admin_role else qs.filter(job__posted_by=u)

    def patch(self, request, *args, **kwargs):
        app = self.get_object()
        st = request.data.get("status")
        if st not in Application.Status.values:
            return Response({"status": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        app.status = st
        app.save(update_fields=["status", "updated_at"])
        return Response(ApplicationSerializer(app, context={"request": request}).data)
