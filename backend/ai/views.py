from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsSeeker
from jobs.models import Job
from resumes.models import Resume
from resumes.services import get_primary_resume

from .interview import evaluate_answer, generate_questions, verdict
from .llm import engine_name, llm_enabled
from .models import CoverLetter, InterviewSession
from .writer import cover_letter, improve_resume


def _resume_or_400(request):
    r = get_primary_resume(request.user)
    if not r:
        return None, Response({"detail": "Please upload your resume first."}, status=400)
    return r, None


def _session_json(s, reveal=False):
    qs = []
    for i, q in enumerate(s.questions):
        a = s.answers.get(str(i))
        item = {"index": i, "question": q["question"], "type": q.get("type"), "skill": q.get("skill"),
                "answered": bool(a)}
        if a:
            item.update({"answer": a["answer"], "result": a["result"]})
        qs.append(item)
    return {"id": s.id, "role": s.role, "job": s.job_id, "questions": qs, "overall_score": s.overall_score,
            "completed": s.completed, "engine": s.engine, "created_at": s.created_at,
            "verdict": verdict(s.overall_score) if s.overall_score is not None else None}


class AIStatusView(APIView):
    def get(self, request):
        return Response({"llm": llm_enabled(), "engine": engine_name()})


class InterviewListCreateView(APIView):
    """GET history / POST {role?, job_id?, count?} -> new mock interview"""
    permission_classes = [IsSeeker]

    def get(self, request):
        items = InterviewSession.objects.filter(user=request.user)[:20]
        return Response([{"id": s.id, "role": s.role, "overall_score": s.overall_score, "completed": s.completed,
                          "questions": len(s.questions), "created_at": s.created_at} for s in items])

    def post(self, request):
        resume, err = _resume_or_400(request)
        if err:
            return err
        job = None
        if request.data.get("job_id"):
            job = Job.objects.filter(id=request.data["job_id"]).first()
        role = (request.data.get("role") or (job.title if job else "")
                or (resume.predicted_roles[0]["role"] if resume.predicted_roles else "Software Developer"))
        n = max(3, min(10, int(request.data.get("count") or 6)))
        skills = list(dict.fromkeys((job.skills if job else []) + resume.skills))
        questions = generate_questions(role, skills, job.description if job else "", n)
        s = InterviewSession.objects.create(user=request.user, role=role[:150], job=job,
                                            questions=questions, engine=engine_name())
        return Response(_session_json(s), status=status.HTTP_201_CREATED)


class InterviewDetailView(APIView):
    permission_classes = [IsSeeker]

    def get(self, request, pk):
        return Response(_session_json(get_object_or_404(InterviewSession, pk=pk, user=request.user)))


class InterviewAnswerView(APIView):
    """POST {index, answer} -> AI feedback for that answer"""
    permission_classes = [IsSeeker]

    def post(self, request, pk):
        s = get_object_or_404(InterviewSession, pk=pk, user=request.user)
        try:
            idx = int(request.data.get("index"))
            q = s.questions[idx]
        except (TypeError, ValueError, IndexError):
            return Response({"detail": "Invalid question."}, status=400)
        answer = (request.data.get("answer") or "").strip()
        if len(answer) < 3:
            return Response({"detail": "Please type your answer."}, status=400)
        result = evaluate_answer(q, answer)
        s.answers[str(idx)] = {"answer": answer[:5000], "result": result}
        scores = [a["result"]["score"] for a in s.answers.values()]
        s.overall_score = round(sum(scores) / len(scores), 1)
        s.completed = len(s.answers) == len(s.questions)
        s.save()
        return Response({"result": result, "session": _session_json(s)})


class ResumeImproverView(APIView):
    """POST {resume_id?} -> improved bullet points + professional summary"""
    permission_classes = [IsSeeker]

    def post(self, request):
        if request.data.get("resume_id"):
            resume = get_object_or_404(Resume, id=request.data["resume_id"], user=request.user, status="done")
        else:
            resume, err = _resume_or_400(request)
            if err:
                return err
        data = improve_resume(resume)
        data["engine"] = engine_name()
        return Response(data)


class CoverLetterView(APIView):
    """GET history / POST {job_id? | job_title, company, description} + tone -> cover letter"""
    permission_classes = [IsSeeker]

    def get(self, request):
        return Response([{"id": c.id, "job_title": c.job_title, "company": c.company, "tone": c.tone,
                          "letter": c.letter, "created_at": c.created_at}
                         for c in CoverLetter.objects.filter(user=request.user)[:20]])

    def post(self, request):
        resume, err = _resume_or_400(request)
        if err:
            return err
        d = request.data
        job = Job.objects.filter(id=d.get("job_id")).first() if d.get("job_id") else None
        title = (job.title if job else d.get("job_title", "")).strip()
        company = (job.company if job else d.get("company", "")).strip() or "your company"
        desc = job.description if job else d.get("description", "")
        if not title:
            return Response({"job_title": "Job title is required."}, status=400)
        tone = d.get("tone") if d.get("tone") in ("professional", "enthusiastic", "confident") else "professional"
        out = cover_letter(resume, request.user, title, company, desc, tone)
        c = CoverLetter.objects.create(user=request.user, job_title=title[:200], company=company[:200],
                                       tone=tone, letter=out["letter"])
        return Response({"id": c.id, "letter": c.letter, "job_title": title, "company": company,
                         "matched_skills": out["matched_skills"], "engine": engine_name()}, status=201)
