import mimetypes

from django.core import signing
from django.http import Http404, HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsSeeker

from .ml.matcher import match_label, match_one, matcher_backend_name
from .ml.learning import resources_for
from .ml.roles import ROLES
from .ml.skill_extractor import category_of
from .models import JDMatch, Resume, SkillProgress
from .serializers import (JDMatchRequestSerializer, JDMatchSerializer,
                          ResumeDetailSerializer, ResumeListSerializer,
                          ResumeUploadSerializer)
from .services import get_primary_resume, process_resume, queue_resume_processing


class ResumeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                    mixins.CreateModelMixin, mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """
    list    GET    /api/resumes/
    upload  POST   /api/resumes/            (multipart: file)
    detail  GET    /api/resumes/{id}/
    delete  DELETE /api/resumes/{id}/
    primary POST   /api/resumes/{id}/set-primary/
    rerun   POST   /api/resumes/{id}/reanalyze/
    """
    permission_classes = [IsSeeker]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = None

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ResumeListSerializer
        if self.action == "create":
            return ResumeUploadSerializer
        return ResumeDetailSerializer

    def create(self, request, *args, **kwargs):
        s = ResumeUploadSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        f = s.validated_data["file"]
        first = not Resume.objects.filter(user=request.user).exists()
        data = f.read()
        f.seek(0)
        resume = Resume.objects.create(user=request.user, file=f, original_name=f.name, is_primary=first,
                                       file_data=data, content_type=getattr(f, "content_type", "") or "")
        queue_resume_processing(resume)
        resume.refresh_from_db()
        return Response(ResumeDetailSerializer(resume, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, pk=None):
        resume = self.get_object()
        Resume.objects.filter(user=request.user).update(is_primary=False)
        resume.is_primary = True
        resume.save(update_fields=["is_primary"])
        return Response({"detail": "Primary resume updated."})

    @action(detail=True, url_path="role-ats")
    def role_ats(self, request, pk=None):
        """GET /api/resumes/{id}/role-ats/?role=Full Stack Developer -> ATS score for that role"""
        from .ml.role_ats import GROUPS, ranking, role_ats
        resume = self.get_object()
        if resume.status != Resume.Status.DONE:
            return Response({"detail": "Resume is not analysed yet."}, status=400)
        top = ranking(resume)
        role = request.query_params.get("role") or top[0]["role"]
        if role not in ROLES:
            return Response({"detail": "Unknown role."}, status=400)
        data = role_ats(resume, role)
        data.update({"groups": GROUPS, "ranking": top})
        return Response(data)

    @action(detail=True, methods=["post"])
    def reanalyze(self, request, pk=None):
        resume = process_resume(self.get_object())
        return Response(ResumeDetailSerializer(resume, context={"request": request}).data)


class ResumeFileView(APIView):
    """GET /api/resumes/file/<signed-token>/  - serves resume from DB (link expires in 7 days)."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        try:
            rid = signing.loads(token, salt="resume-file", max_age=60 * 60 * 24 * 7)
        except signing.BadSignature:
            raise Http404("Link expired")
        r = get_object_or_404(Resume, id=rid)
        if r.file_data:
            data, ctype = bytes(r.file_data), r.content_type
        else:
            try:
                with r.file.open("rb") as fh:
                    data = fh.read()
            except Exception:
                raise Http404("File not available")
            ctype = ""
        ctype = ctype or mimetypes.guess_type(r.original_name)[0] or "application/octet-stream"
        resp = HttpResponse(data, content_type=ctype)
        resp["Content-Disposition"] = f'inline; filename="{r.original_name}"'
        return resp


class JDMatchView(APIView):
    """Check resume against any pasted job description."""
    permission_classes = [IsSeeker]

    def post(self, request):
        s = JDMatchRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        if d.get("resume_id"):
            resume = get_object_or_404(Resume, id=d["resume_id"], user=request.user, status=Resume.Status.DONE)
        else:
            resume = get_primary_resume(request.user)
        if not resume:
            return Response({"detail": "Please upload a resume first."}, status=400)

        text = f"{d.get('job_title', '')}\n{d['job_description']}"
        result = match_one(resume.raw_text, resume.skills, resume.experience_years, text)
        result["label"] = match_label(result["score"])
        result["engine"] = matcher_backend_name()
        m = JDMatch.objects.create(user=request.user, resume=resume, job_title=d.get("job_title", ""),
                                   job_description=d["job_description"], score=result["score"], result=result)
        return Response(JDMatchSerializer(m).data, status=201)


class JDMatchHistoryView(ListAPIView):
    permission_classes = [IsSeeker]
    serializer_class = JDMatchSerializer

    def get_queryset(self):
        return JDMatch.objects.filter(user=self.request.user).select_related("resume")


class RoadmapView(APIView):
    """
    GET  /api/resumes/roadmap/?role=Python Developer
         Week-by-week learning plan for the skills the student is missing for a role.
    POST /api/resumes/roadmap/  {"skill": "Docker", "done": true}   mark a skill learned / not learned
    """
    permission_classes = [IsSeeker]

    def get(self, request):
        resume = get_primary_resume(request.user)
        have = {s.lower() for s in (resume.skills if resume else [])}
        learned = set(SkillProgress.objects.filter(user=request.user).values_list("skill", flat=True))
        predicted = [r["role"] for r in (resume.predicted_roles if resume else [])]
        role = request.query_params.get("role") or (predicted[0] if predicted else "Full Stack Developer")
        if role not in ROLES:
            return Response({"detail": "Unknown role."}, status=400)

        core, bonus = ROLES[role]
        steps, week = [], 1
        for priority, skills in (("core", core), ("bonus", bonus)):
            for skill in skills:
                if skill.lower() in have:
                    continue
                info = resources_for(skill)
                steps.append({
                    "skill": skill, "category": category_of(skill), "priority": priority,
                    "week_start": week, "week_end": week + info["weeks"] - 1,
                    "done": skill in learned, **info,
                })
                week += info["weeks"]

        already = [s for s in core + bonus if s.lower() in have]
        total = len(core) + len(bonus)
        done_now = len(already) + sum(1 for s in steps if s["done"])
        return Response({
            "role": role,
            "roles": list(ROLES.keys()),
            "suggested_roles": predicted,
            "has_resume": bool(resume),
            "already_have": already,
            "steps": steps,
            "total_weeks": max(0, week - 1),
            "remaining_weeks": sum(s["weeks"] for s in steps if not s["done"]),
            "readiness": round(done_now / total * 100) if total else 0,
        })

    def post(self, request):
        skill = (request.data.get("skill") or "").strip()[:80]
        if not skill:
            return Response({"detail": "skill is required"}, status=400)
        if request.data.get("done", True):
            SkillProgress.objects.get_or_create(user=request.user, skill=skill)
        else:
            SkillProgress.objects.filter(user=request.user, skill=skill).delete()
        return Response({"skill": skill, "done": bool(request.data.get("done", True))})
