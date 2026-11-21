"""Run:  python manage.py test"""
from unittest import mock
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from jobs.models import Job
from resumes.ml.analyzer import analyze_resume
from resumes.ml.matcher import match_one
from resumes.ml.parser import extract_phone, parse_resume_text
from resumes.ml.roles import predict_roles
from resumes.ml.skill_extractor import extract_skills

RESUME = """Asha Kulkarni
asha.k@gmail.com | +91 91234 56789 | github.com/asha-k | linkedin.com/in/asha-k
SUMMARY
Python developer who built and deployed Django REST APIs.
SKILLS
Python, Django, PostgreSQL, React, Docker, Git, C, R
EXPERIENCE
Backend Intern - Acme   Jan 2024 - Dec 2024
- Developed 10+ APIs and reduced load time by 30%.
- Optimized SQL queries; automated deployments with Docker.
PROJECTS
Chat app using React and Django Channels
EDUCATION
MCA, Pune University 2023 - 2025
"""


class MLTests(TestCase):
    def test_skill_extraction(self):
        s = extract_skills(RESUME)["skills"]
        for k in ["Python", "Django", "PostgreSQL", "React", "Docker", "C", "R"]:
            self.assertIn(k, s)
        self.assertNotIn("Go", extract_skills("I will go to the market")["skills"])
        self.assertNotIn("CSS", extract_skills("Tailwind CSS expert")["skills"])

    def test_parser(self):
        p = parse_resume_text(RESUME)
        self.assertEqual(p["name"], "Asha Kulkarni")
        self.assertEqual(p["email"], "asha.k@gmail.com")
        self.assertIn("MCA", p["education"])
        self.assertAlmostEqual(p["experience_years"], 0.9, delta=0.2)
        self.assertIn("skills", p["sections"])
        self.assertEqual(extract_phone("call 9876543210 now"), "9876543210")

    def test_analyzer_and_roles(self):
        p = parse_resume_text(RESUME)
        skills = extract_skills(p["text"])["skills"]
        a = analyze_resume(p, skills)
        self.assertTrue(0 < a["score"] <= 100)
        self.assertEqual(predict_roles(skills)[0]["role"] in
                         ("Python Developer", "Backend Developer", "Full Stack Developer"), True)

    def test_matcher_ranks_relevant_job_higher(self):
        skills = extract_skills(RESUME)["skills"]
        good = match_one(RESUME, skills, 1, "Python Django developer with PostgreSQL and Docker")
        bad = match_one(RESUME, skills, 1, "Senior accountant with Tally and GST filing experience")
        self.assertGreater(good["score"], bad["score"])
        self.assertIn("Django", good["matched_skills"])


@override_settings(ADZUNA_APP_ID="x", ADZUNA_APP_KEY="y", ASYNC_PROCESSING=False, FREE_JOB_APIS=False)
class APIFlowTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        r = self.c.post("/api/auth/register/", {"username": "asha", "email": "asha@x.com",
                                                 "password": "secret12", "role": "seeker"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.c.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

    def _upload(self):
        f = SimpleUploadedFile("cv.txt", RESUME.encode(), content_type="text/plain")
        return self.c.post("/api/resumes/", {"file": f}, format="multipart")

    def test_upload_and_live_jobs_with_mocked_adzuna(self):
        r = self._upload()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], "done")
        self.assertGreater(r.data["ats_score"], 50)

        fake = mock.Mock()
        fake.raise_for_status.return_value = None
        fake.json.return_value = {"results": [{
            "id": 111, "title": "Python Django Developer", "company": {"display_name": "Foo"},
            "location": {"display_name": "Pune"}, "description": "Python Django PostgreSQL Docker",
            "redirect_url": "https://example.com/j/111", "created": "2026-11-01T10:00:00Z"}]}
        with mock.patch("jobs.services.providers.requests.get", return_value=fake):
            r = self.c.get("/api/jobs/live/?refresh=1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("adzuna", r.data["meta"]["providers"])
        self.assertEqual(r.data["results"][0]["job"]["source"], "adzuna")
        self.assertTrue(Job.objects.filter(source="adzuna", external_id="111").exists())

    def test_jd_match(self):
        self._upload()
        r = self.c.post("/api/resumes/match-jd/", {"job_description": "Need Python, Django, AWS and Kubernetes skills for backend role"},
                        format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("AWS", r.data["result"]["missing_skills"])

    def test_role_permissions(self):
        r = self.c.post("/api/jobs/", {"title": "x", "description": "y"}, format="json")
        self.assertEqual(r.status_code, 403)
        User = get_user_model()
        User.objects.create_user("hr", "hr@x.com", "secret12", role="recruiter", company_name="X")
        c2 = APIClient()
        tok = c2.post("/api/auth/login/", {"username": "hr", "password": "secret12"}, format="json").data["access"]
        c2.credentials(HTTP_AUTHORIZATION="Bearer " + tok)
        r = c2.post("/api/jobs/", {"title": "Django Dev", "description": "Python Django REST API PostgreSQL"},
                    format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("Django", r.data["skills"])
        self._upload()
        r = self.c.post(f"/api/jobs/{r.data['id']}/apply/", format="json")
        self.assertEqual(r.status_code, 201)


REMOTIVE = {"job-count": 1, "jobs": [{
    "id": 501, "url": "https://remotive.com/remote-jobs/software-dev/python-django-dev-501",
    "title": "Python Django Developer", "company_name": "RemoteCo", "category": "Software Development",
    "job_type": "full_time", "publication_date": "2026-11-18T10:00:00",
    "candidate_required_location": "Worldwide", "salary": "",
    "description": "<p>We need <b>Python</b>, Django, PostgreSQL &amp; Docker.</p><ul><li>REST APIs</li></ul>"}]}
JOBICY = {"jobCount": 1, "jobs": [{
    "id": 77, "url": "https://jobicy.com/jobs/77-react-developer", "jobTitle": "React Developer &#8211; Remote",
    "companyName": "Jobi Inc", "jobType": ["Full-Time"], "jobGeo": "APAC",
    "jobDescription": "<p>React, TypeScript and REST API</p>", "pubDate": "2026-11-17T08:00:00+00:00"}]}
ARBEITNOW = {"data": [
    {"slug": "python-backend-berlin-1", "company_name": "Arb GmbH", "title": "Python Backend Engineer",
     "description": "<p>Python FastAPI</p>", "remote": True, "url": "https://www.arbeitnow.com/jobs/python-backend-berlin-1",
     "tags": ["Python"], "job_types": ["full-time"], "location": "Berlin", "created_at": 1763460000},
    {"slug": "sales-1", "company_name": "X", "title": "Sales Manager", "description": "sales", "remote": False,
     "url": "https://www.arbeitnow.com/jobs/sales-1", "tags": [], "job_types": [], "location": "Munich", "created_at": 1763460000}]}


def _fake_get(url, *a, **k):
    m = mock.Mock()
    m.raise_for_status.return_value = None
    m.json.return_value = REMOTIVE if "remotive" in url else JOBICY if "jobicy" in url else ARBEITNOW
    return m


class FreeProvidersTests(TestCase):
    def test_parsers(self):
        from jobs.services.providers import ArbeitnowProvider, JobicyProvider, RemotiveProvider, keyword_for
        self.assertEqual(keyword_for("Python Developer"), "python")
        self.assertEqual(keyword_for("Full Stack Developer"), "full stack")
        with mock.patch("jobs.services.providers.requests.get", side_effect=_fake_get):
            r = RemotiveProvider().search("Python Developer")[0]
            j = JobicyProvider().search("React Developer")[0]
            a = ArbeitnowProvider().search("Python Developer")
        self.assertEqual(r["apply_url"], "https://remotive.com/remote-jobs/software-dev/python-django-dev-501")
        self.assertIn("PostgreSQL & Docker", r["description"])
        self.assertEqual(r["work_mode"], "remote")
        self.assertEqual(j["title"], "React Developer \u2013 Remote")
        self.assertEqual(len(a), 1)  # sales job filtered out
        self.assertEqual(a[0]["apply_url"], "https://www.arbeitnow.com/jobs/python-backend-berlin-1")


@override_settings(ADZUNA_APP_ID="", ADZUNA_APP_KEY="", JSEARCH_API_KEY="", FREE_JOB_APIS=True)
class LiveFeedTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        r = self.c.post("/api/auth/register/", {"username": "dev", "email": "dev@x.com",
                                                 "password": "secret12", "role": "seeker"}, format="json")
        self.c.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
        f = SimpleUploadedFile("cv.txt", RESUME.encode(), content_type="text/plain")
        self.resume = self.c.post("/api/resumes/", {"file": f}, format="multipart").data
        Job.objects.create(source="demo", external_id="d1", title="Python Developer",
                           description="Python Django PostgreSQL", skills=["Python", "Django"])

    def test_real_jobs_shown_and_demo_hidden(self):
        with mock.patch("jobs.services.providers.requests.get", side_effect=_fake_get):
            r = self.c.get("/api/jobs/live/?q=python developer&refresh=1")
        self.assertEqual(r.status_code, 200)
        sources = {x["job"]["source"] for x in r.data["results"]}
        self.assertIn("remotive", sources)
        self.assertNotIn("demo", sources)
        for x in r.data["results"]:
            self.assertTrue(x["job"]["apply_url"].startswith("https://"))

    def test_all_providers_down_falls_back_to_demo(self):
        with mock.patch("jobs.services.providers.requests.get", side_effect=ConnectionError("offline")):
            r = self.c.get("/api/jobs/live/?refresh=1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["meta"]["errors"]), 3)
        self.assertIn("demo", {x["job"]["source"] for x in r.data["results"]})

    def test_resume_file_served_from_database(self):
        url = self.resume["file_url"]
        r = APIClient().get(url.replace("http://testserver", ""))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Asha Kulkarni", r.content)
        self.assertEqual(APIClient().get("/api/resumes/file/bad-token/").status_code, 404)


class RoleAccessTests(TestCase):
    def test_public_signup_is_always_seeker(self):
        c = APIClient()
        r = c.post("/api/auth/register/", {"username": "hacker", "email": "h@x.com", "password": "secret12",
                                           "role": "recruiter", "company_name": "Fake"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["user"]["role"], "seeker")
        c.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
        self.assertEqual(c.post("/api/jobs/", {"title": "x", "description": "y"}, format="json").status_code, 403)
        self.assertEqual(c.post("/api/auth/users/create/", {}, format="json").status_code, 403)

    def test_admin_creates_recruiter(self):
        User = get_user_model()
        User.objects.create_superuser("boss", "b@x.com", "secret12")
        c = APIClient()
        tok = c.post("/api/auth/login/", {"username": "boss", "password": "secret12"}, format="json").data["access"]
        c.credentials(HTTP_AUTHORIZATION="Bearer " + tok)
        r = c.post("/api/auth/users/create/", {"username": "hr1", "email": "hr1@x.com", "password": "secret12",
                                               "role": "recruiter", "company_name": "Acme"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["role"], "recruiter")

    def test_demo_account_password_locked(self):
        User = get_user_model()
        User.objects.create_user("student", "s@x.com", "student123")
        c = APIClient()
        tok = c.post("/api/auth/login/", {"username": "student", "password": "student123"}, format="json").data["access"]
        c.credentials(HTTP_AUTHORIZATION="Bearer " + tok)
        r = c.post("/api/auth/change-password/", {"old_password": "student123", "new_password": "hacked123"}, format="json")
        self.assertEqual(r.status_code, 403)


class RoadmapTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        r = self.c.post("/api/auth/register/", {"username": "learner", "email": "l@x.com", "password": "secret12"}, format="json")
        self.c.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
        f = SimpleUploadedFile("cv.txt", RESUME.encode(), content_type="text/plain")
        self.c.post("/api/resumes/", {"file": f}, format="multipart")

    def test_roadmap_lists_missing_skills_and_tracks_progress(self):
        r = self.c.get("/api/resumes/roadmap/?role=DevOps Engineer")
        self.assertEqual(r.status_code, 200)
        skills = [s["skill"] for s in r.data["steps"]]
        self.assertIn("Kubernetes", skills)
        self.assertNotIn("Docker", skills)          # already in resume
        self.assertIn("Docker", r.data["already_have"])
        self.assertTrue(r.data["steps"][0]["links"][0]["url"].startswith("https://"))
        before = r.data["readiness"]
        self.c.post("/api/resumes/roadmap/", {"skill": "Kubernetes", "done": True}, format="json")
        r2 = self.c.get("/api/resumes/roadmap/?role=DevOps Engineer")
        self.assertGreater(r2.data["readiness"], before)
        self.assertTrue(next(s for s in r2.data["steps"] if s["skill"] == "Kubernetes")["done"])
        self.assertEqual(self.c.get("/api/resumes/roadmap/?role=Astronaut").status_code, 400)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.User.objects.create_user("riya", "riya@x.com", "oldpass12", first_name="Riya")
        self.c = APIClient()

    def _code_from_mail(self):
        import re
        from django.core import mail
        return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

    @override_settings(EMAIL_HOST_USER="me@gmail.com", EMAIL_HOST_PASSWORD="abcdabcdabcdabcd")
    def test_otp_flow_with_email(self):
        from django.core import mail
        with patch("accounts.emails._smtp", side_effect=lambda to, s, t, h: (mail.send_mail(s, t, "a@b.c", [to]), (True, ""))[1]):
            r = self.c.post("/api/auth/password-reset/", {"email": "RIYA@x.com"}, format="json")
            self.assertEqual(r.status_code, 200, r.data)
            self.assertNotIn("dev_code", r.data)
            code = self._code_from_mail()
            # resend too soon
            self.assertEqual(self.c.post("/api/auth/password-reset/", {"email": "riya@x.com"}, format="json").status_code, 429)
            wrong = "000000" if code != "000000" else "111111"
            r = self.c.post("/api/auth/password-reset/verify/", {"email": "riya@x.com", "code": wrong}, format="json")
            self.assertEqual(r.status_code, 400)
            self.assertIn("4 attempts left", r.data["code"][0])
            r = self.c.post("/api/auth/password-reset/verify/", {"email": "riya@x.com", "code": code}, format="json")
            self.assertEqual(r.status_code, 200)
            r = self.c.post("/api/auth/password-reset/confirm/", {"email": "riya@x.com", "code": code,
                                                                  "new_password": "newpass12"}, format="json")
            self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(self.User.objects.get(username="riya").check_password("newpass12"))
        # code works only once
        r = self.c.post("/api/auth/password-reset/confirm/", {"email": "riya@x.com", "code": code,
                                                              "new_password": "another12"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_unknown_email_and_lockout(self):
        self.assertEqual(self.c.post("/api/auth/password-reset/", {"email": "nobody@x.com"}, format="json").status_code, 404)

    @override_settings(DEBUG=True)
    def test_dev_mode_shows_code_when_email_not_set_up(self):
        r = self.c.post("/api/auth/password-reset/", {"email": "riya@x.com"}, format="json")
        self.assertEqual(r.status_code, 200)
        code = r.data["dev_code"]
        for _ in range(5):
            self.c.post("/api/auth/password-reset/verify/", {"email": "riya@x.com", "code": "x"}, format="json")
        r = self.c.post("/api/auth/password-reset/confirm/", {"email": "riya@x.com", "code": code,
                                                              "new_password": "newpass12"}, format="json")
        self.assertEqual(r.status_code, 400)  # locked after 5 wrong attempts

    def test_production_without_email_gives_clear_error(self):
        r = self.c.post("/api/auth/password-reset/", {"email": "riya@x.com"}, format="json")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.data["code"], "email_not_configured")

    @override_settings(BREVO_API_KEY="bad", EMAIL_FROM_ADDRESS="me@gmail.com")
    def test_brevo_error_is_reported(self):
        class R:
            status_code = 400
            text = "sender not valid"
            def json(self):
                return {"message": "Sender me@gmail.com is not valid"}
        admin = self.User.objects.create_user("boss", "boss@x.com", "secret12", role="admin")
        self.c.force_authenticate(admin)
        with patch("accounts.emails.requests.post", return_value=R()):
            r = self.c.post("/api/auth/email/test/", {"to": "boss@x.com"}, format="json")
            self.assertEqual(r.status_code, 502)
            self.assertIn("Verify me@gmail.com", r.data["detail"])
            self.assertEqual(self.c.get("/api/auth/email/status/").data["provider"], "brevo")
            self.c.force_authenticate(None)
            r = self.c.post("/api/auth/password-reset/", {"email": "riya@x.com"}, format="json")
            self.assertEqual(r.status_code, 502)


SUPPORT_RESUME = """Priya Shinde
priya.s@gmail.com | +91 99887 66554
SUMMARY
Technical Support Engineer with 1 year of experience resolving customer issues.
SKILLS
Troubleshooting, Windows, Active Directory, ServiceNow, ITIL, Remote Desktop, Customer Service, Computer Networks
EXPERIENCE
Technical Support Engineer - HelpCo   Jan 2024 - Dec 2024
- Resolved 40+ customer tickets daily within SLA using ServiceNow.
- Troubleshooted Windows, printer and network issues and escalated L2 cases.
EDUCATION
BCA, Pune University 2020 - 2023
"""


class RoleATSTests(TestCase):
    def _client(self, text, username):
        c = APIClient()
        r = c.post("/api/auth/register/", {"username": username, "email": f"{username}@x.com", "password": "secret12"}, format="json")
        c.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
        rid = c.post("/api/resumes/", {"file": SimpleUploadedFile("cv.txt", text.encode())}, format="multipart").data["id"]
        return c, rid

    def test_same_resume_scores_differently_per_role(self):
        c, rid = self._client(RESUME, "dev1")
        dev = c.get(f"/api/resumes/{rid}/role-ats/?role=Python Developer").data
        sup = c.get(f"/api/resumes/{rid}/role-ats/?role=Technical Support Engineer").data
        self.assertGreater(dev["score"], sup["score"])
        self.assertIn("Troubleshooting", sup["missing_core"])
        self.assertTrue(sup["tips"])
        self.assertIn("Support", dev["groups"])

    def test_support_resume_ranks_support_roles_first(self):
        c, rid = self._client(SUPPORT_RESUME, "sup1")
        r = c.get(f"/api/resumes/{rid}/role-ats/").data
        self.assertIn(r["ranking"][0]["role"], ("Technical Support Engineer", "IT Support / Helpdesk"))
        sup = c.get(f"/api/resumes/{rid}/role-ats/?role=Technical Support Engineer").data
        self.assertGreaterEqual(sup["score"], 65)
        self.assertTrue(sup["title_match"])
        self.assertEqual(c.get(f"/api/resumes/{rid}/role-ats/?role=Astronaut").status_code, 400)
