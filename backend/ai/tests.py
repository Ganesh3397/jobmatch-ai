from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from jobs.models import Job
from resumes.tests import RESUME


@override_settings(GEMINI_API_KEY="")
class AIRuleEngineTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        r = self.c.post("/api/auth/register/", {"username": "ai_user", "email": "ai@x.com", "password": "secret12",
                                                 "first_name": "Asha"}, format="json")
        self.c.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
        self.c.post("/api/resumes/", {"file": SimpleUploadedFile("cv.txt", RESUME.encode())}, format="multipart")

    def test_mock_interview_flow(self):
        r = self.c.post("/api/ai/interviews/", {"count": 5}, format="json")
        self.assertEqual(r.status_code, 201)
        sid, qs = r.data["id"], r.data["questions"]
        self.assertEqual(len(qs), 5)
        self.assertEqual(qs[0]["type"], "hr")
        good = ("In my project I built a Django REST API. For example I used select_related and prefetch_related "
                "to reduce queries from 120 to 8, which improved response time by 60%. The view, url and middleware "
                "process the request and return a response. Situation task action result: we solved it as a team.")
        r = self.c.post(f"/api/ai/interviews/{sid}/answer/", {"index": 1, "answer": good}, format="json")
        self.assertEqual(r.status_code, 200)
        good_score = r.data["result"]["score"]
        r = self.c.post(f"/api/ai/interviews/{sid}/answer/", {"index": 2, "answer": "I don't know"}, format="json")
        self.assertLess(r.data["result"]["score"], good_score)
        self.assertTrue(r.data["result"]["improvements"])
        for i in (0, 3, 4):
            self.c.post(f"/api/ai/interviews/{sid}/answer/", {"index": i, "answer": good}, format="json")
        d = self.c.get(f"/api/ai/interviews/{sid}/").data
        self.assertTrue(d["completed"])
        self.assertIsNotNone(d["verdict"])
        self.assertEqual(len(self.c.get("/api/ai/interviews/").data), 1)

    def test_resume_improver(self):
        r = self.c.post("/api/ai/improve-resume/", {}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["summary"])
        for it in r.data["items"]:
            self.assertNotEqual(it["original"], it["improved"])

    def test_cover_letter_for_job_and_manual(self):
        job = Job.objects.create(source="internal", title="Django Developer", company="Acme",
                                 description="Python Django PostgreSQL Docker REST API", skills=["Python", "Django"])
        r = self.c.post("/api/ai/cover-letters/", {"job_id": job.id, "tone": "enthusiastic"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("Acme", r.data["letter"])
        self.assertIn("Django", r.data["letter"])
        r = self.c.post("/api/ai/cover-letters/", {"job_title": "Data Analyst", "company": "Beta"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(self.c.get("/api/ai/cover-letters/").data), 2)
        self.assertEqual(self.c.post("/api/ai/cover-letters/", {}, format="json").status_code, 400)


@override_settings(GEMINI_API_KEY="test-key")
class GeminiTests(TestCase):
    def test_gemini_used_when_key_set_and_fallback_on_error(self):
        from ai.interview import generate_questions
        fake = mock.Mock()
        fake.raise_for_status.return_value = None
        fake.json.return_value = {"candidates": [{"content": {"parts": [{"text":
            '{"questions":[{"question":"Q1 from Gemini?","type":"hr","skill":"x","points":["a"]},'
            '{"question":"Q2?","type":"technical","skill":"Python","points":["b"]},'
            '{"question":"Q3?","type":"technical","skill":"SQL","points":["c"]}]}'}]}}]}
        with mock.patch("ai.llm.requests.post", return_value=fake):
            qs = generate_questions("Python Developer", ["Python"], "", 3)
        self.assertEqual(qs[0]["question"], "Q1 from Gemini?")
        with mock.patch("ai.llm.requests.post", side_effect=ConnectionError("down")):
            qs = generate_questions("Python Developer", ["Python", "SQL"], "", 4)
        self.assertEqual(len(qs), 4)  # rule engine fallback
