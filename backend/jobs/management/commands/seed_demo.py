"""
python manage.py seed_demo

Creates demo users, demo jobs, recruiter job posts, a sample resume and
applications so the project can be demonstrated even without API keys.
All company names are fictional.
"""
import random
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import Application, Job, SavedJob
from resumes.ml.matcher import match_label, match_one
from resumes.models import Resume
from resumes.services import process_resume

User = get_user_model()

COMPANIES = ["TechNova Solutions", "CloudNine Labs", "DataSphere Analytics", "PixelCraft Studios",
             "InfoBridge Systems", "NextGen Softwares", "BrightPath Technologies", "CodeNest Pvt Ltd",
             "Quantum Leap IT", "BlueOrbit Digital", "Sahyadri Infotech", "Deccan Data Works"]
CITIES = ["Pune", "Mumbai", "Bengaluru", "Hyderabad", "Nashik", "Nagpur", "Chennai", "Noida"]

TEMPLATES = [
    ("Python Developer", ["Python", "Django", "REST API", "PostgreSQL", "Git"], 1, "full_time"),
    ("Junior Python Django Developer", ["Python", "Django", "Django REST Framework", "MySQL", "HTML", "CSS"], 0, "full_time"),
    ("Full Stack Developer (React + Django)", ["React", "JavaScript", "Django", "PostgreSQL", "REST API", "Docker"], 2, "full_time"),
    ("Full Stack Developer Intern", ["React", "Node.js", "MongoDB", "JavaScript", "Git"], 0, "internship"),
    ("Frontend Developer - React", ["React", "JavaScript", "TypeScript", "Redux", "HTML", "CSS", "Tailwind CSS"], 1, "full_time"),
    ("Backend Engineer", ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Microservices"], 3, "full_time"),
    ("Java Spring Boot Developer", ["Java", "Spring Boot", "Hibernate", "MySQL", "Microservices", "REST API"], 2, "full_time"),
    ("Data Analyst", ["SQL", "Excel", "Power BI", "Python", "Pandas", "Data Analysis"], 0, "full_time"),
    ("Data Scientist", ["Python", "Machine Learning", "Scikit-learn", "Pandas", "Statistics", "SQL"], 2, "full_time"),
    ("Machine Learning Engineer", ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Docker"], 2, "full_time"),
    ("AI Engineer - Generative AI", ["Python", "Generative AI", "LangChain", "NLP", "FastAPI", "Prompt Engineering"], 1, "full_time"),
    ("ML Intern", ["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-learn"], 0, "internship"),
    ("DevOps Engineer", ["Linux", "Docker", "Kubernetes", "AWS", "CI/CD", "Jenkins", "Terraform"], 3, "full_time"),
    ("Cloud Support Associate", ["AWS", "Linux", "Computer Networks", "Bash"], 0, "full_time"),
    ("Android Developer", ["Android", "Kotlin", "Java", "Firebase", "REST API"], 1, "full_time"),
    ("Flutter Developer", ["Flutter", "Dart", "Firebase", "REST API", "Git"], 1, "full_time"),
    ("QA Automation Engineer", ["Selenium", "Java", "Unit Testing", "Postman", "Jira", "Agile"], 2, "full_time"),
    ("Software Engineer Trainee", ["Java", "Python", "SQL", "DSA", "OOP", "Git"], 0, "full_time"),
    ("Node.js Developer", ["Node.js", "Express.js", "MongoDB", "JavaScript", "REST API"], 2, "full_time"),
    ("Business Intelligence Developer", ["SQL", "Power BI", "Tableau", "Excel", "Data Analysis"], 2, "contract"),
]

INTRO = [
    "We are looking for a passionate {title} to join our growing engineering team in {city}.",
    "{company} is hiring a {title} to build scalable products used by thousands of customers.",
    "Join {company} as a {title} and work on exciting real-world projects with a modern tech stack.",
]
RESP = [
    "Design, develop and maintain high quality applications.",
    "Collaborate with product managers, designers and other developers.",
    "Write clean, testable and well documented code.",
    "Participate in code reviews and agile ceremonies.",
    "Troubleshoot, debug and optimise existing systems.",
]

SAMPLE_RESUME = """Rahul Patil
Pune, Maharashtra | rahul.patil.dev@gmail.com | +91 98765 43210
linkedin.com/in/rahulpatil-dev | github.com/rahulpatil-dev

PROFESSIONAL SUMMARY
MCA student and aspiring Full Stack Python Developer with hands-on experience building web
applications using Python, Django, React and PostgreSQL. Passionate about AI/ML and clean code.

TECHNICAL SKILLS
Languages: Python, JavaScript, Java, SQL
Frameworks: Django, Django REST Framework, React, Bootstrap
Databases: PostgreSQL, MySQL, Redis
Tools: Git, GitHub, Postman, VS Code, Linux
AI/ML: Machine Learning, Pandas, NumPy, Scikit-learn

EXPERIENCE
Python Developer Intern - CodeNest Pvt Ltd, Pune        Jun 2025 - Dec 2025
- Developed 12+ REST APIs using Django REST Framework for an e-commerce platform.
- Optimized PostgreSQL queries and reduced API response time by 35%.
- Built reusable React components and integrated them with backend APIs.
- Collaborated with a team of 6 developers using Git and Agile methodology.

PROJECTS
AI Resume Analyzer (Python, Django, React, PostgreSQL, Scikit-learn)
- Built a system that parses resumes and matches them with job descriptions using NLP.
Student Attendance System (Python, OpenCV)
- Implemented face recognition based attendance used by 200+ students.

EDUCATION
MCA - Savitribai Phule Pune University, 2024 - 2026 (CGPA 8.4)
BCA - Fergusson College, Pune, 2021 - 2024 (78%)

CERTIFICATIONS
Python for Everybody - Coursera
Communication, Teamwork, Problem Solving
"""


def make_pdf(path: Path, text: str):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    doc = fitz.open()
    page = doc.new_page()
    y = 50
    for line in text.splitlines():
        if y > 800:
            page, y = doc.new_page(), 50
        bold = line.isupper() and line.strip()
        page.insert_text((50, y), line, fontsize=12 if bold else 10, fontname="hebo" if bold else "helv")
        y += 16 if bold else 13
    doc.save(str(path))
    doc.close()


def _attach(resume, path):
    """Save the PDF on disk AND in the database (cloud-safe)."""
    with open(path, "rb") as fh:
        data = fh.read()
        fh.seek(0)
        resume.file_data = data
        resume.content_type = "application/pdf"
        resume.file.save(path.name, File(fh), save=True)


class Command(BaseCommand):
    help = "Seed demo users, jobs, a sample resume and applications."

    def add_arguments(self, parser):
        parser.add_argument("--if-empty", action="store_true",
                            help="Do nothing if the database already has users (safe for every deploy).")

    def handle(self, *args, **opts):
        if opts["if_empty"] and User.objects.exists():
            self.stdout.write("Database already has data - skipping demo seed.")
            return
        random.seed(7)
        import os
        admin_pw = os.getenv("ADMIN_PASSWORD") or ("admin123" if settings.DEBUG else None)
        if admin_pw:
            admin, _ = User.objects.get_or_create(username="admin", defaults={
                "email": "admin@jobmatch.ai", "first_name": "Site", "last_name": "Admin",
                "is_staff": True, "is_superuser": True})
            admin.set_password(admin_pw)
            admin.save()
        else:
            self.stdout.write(self.style.WARNING("ADMIN_PASSWORD not set - admin user not created."))

        recruiters = []
        for i, comp in enumerate(["TechNova Solutions", "DataSphere Analytics"], start=1):
            r, _ = User.objects.get_or_create(username=f"recruiter{i}" if i > 1 else "recruiter", defaults={
                "email": f"hr{i}@{comp.split()[0].lower()}.com", "role": "recruiter",
                "first_name": ["Priya", "Amit"][i - 1], "last_name": ["Sharma", "Kulkarni"][i - 1],
                "company_name": comp, "location": "Pune"})
            r.set_password("recruiter123")
            r.save()
            recruiters.append(r)

        seeker, _ = User.objects.get_or_create(username="student", defaults={
            "email": "rahul.patil.dev@gmail.com", "role": "seeker", "first_name": "Rahul",
            "last_name": "Patil", "location": "Pune", "headline": "MCA Student | Python Full Stack"})
        seeker.set_password("student123")
        seeker.save()

        # ---------- demo jobs (simulate live feed)
        Job.objects.filter(source=Job.Source.DEMO).delete()
        n = 0
        for title, skills, exp, jtype in TEMPLATES:
            for _ in range(2):
                comp, city = random.choice(COMPANIES), random.choice(CITIES)
                mode = random.choice(["onsite", "onsite", "hybrid", "remote"])
                desc = " ".join([
                    random.choice(INTRO).format(title=title, city=city, company=comp),
                    "\n\nResponsibilities:\n- " + "\n- ".join(random.sample(RESP, 3)),
                    "\n\nRequired skills: " + ", ".join(skills) + ".",
                    f"\nExperience: {exp}+ years." if exp else "\nFreshers are welcome to apply.",
                ])
                base = 300000 + exp * 250000 + random.randint(0, 4) * 50000
                Job.objects.create(
                    source=Job.Source.DEMO, external_id=f"demo-{n}", title=title, company=comp,
                    location=city if mode != "remote" else "Remote (India)", description=desc,
                    skills=skills, job_type=jtype, work_mode=mode, min_experience=exp,
                    salary_min=None if jtype == "internship" else base,
                    salary_max=None if jtype == "internship" else base + 300000,
                    posted_at=timezone.now() - timezone.timedelta(hours=random.randint(1, 240)),
                )
                n += 1

        # ---------- recruiter posts on platform
        Job.objects.filter(source=Job.Source.INTERNAL, posted_by__in=recruiters).delete()
        internal = []
        for r, (title, skills, exp, jtype) in zip(recruiters * 2, TEMPLATES[:4]):
            internal.append(Job.objects.create(
                source=Job.Source.INTERNAL, posted_by=r, title=title, company=r.company_name,
                location="Pune", work_mode="hybrid", job_type=jtype, min_experience=exp, skills=skills,
                description=f"{r.company_name} is hiring a {title}.\n\nMust have: {', '.join(skills)}.\n"
                            f"Good communication and problem solving skills required.",
                salary_min=400000 if jtype != "internship" else None,
                salary_max=800000 if jtype != "internship" else None,
            ))

        # ---------- sample resume
        sample_dir = Path(settings.BASE_DIR).parent / "sample_resumes"
        sample_dir.mkdir(exist_ok=True)
        pdf_path = sample_dir / "Rahul_Patil_Resume.pdf"
        make_pdf(pdf_path, SAMPLE_RESUME)

        Resume.objects.filter(user=seeker).delete()
        res = Resume(user=seeker, original_name=pdf_path.name, is_primary=True)
        _attach(res, pdf_path)
        process_resume(res)

        # ---------- some applications from extra demo seekers
        Application.objects.filter(job__in=internal).delete()
        for i, (fname, extra) in enumerate([("Sneha", "React TypeScript Redux"), ("Omkar", "Java Spring Boot"),
                                            ("Pooja", "Python Machine Learning Pandas")]):
            u, _ = User.objects.get_or_create(username=f"demo_seeker{i}", defaults={
                "email": f"demo{i}@example.com", "role": "seeker", "first_name": fname, "last_name": "Demo"})
            u.set_password("student123")
            u.save()
            txt = sample_dir / f"{fname}_Resume.pdf"
            make_pdf(txt, SAMPLE_RESUME.replace("Rahul Patil", f"{fname} Demo")
                     .replace("rahul.patil.dev@gmail.com", u.email)
                     .replace("Languages: Python, JavaScript, Java, SQL", f"Languages: {extra}, SQL"))
            Resume.objects.filter(user=u).delete()
            rr = Resume(user=u, original_name=txt.name, is_primary=True)
            _attach(rr, txt)
            process_resume(rr)
            for job in internal[:3]:
                m = match_one(rr.raw_text, rr.skills, rr.experience_years, job.text_for_matching,
                              job.skills, job.min_experience)
                m["label"] = match_label(m["score"])
                Application.objects.get_or_create(job=job, seeker=u, defaults={
                    "resume": rr, "match_score": m["score"], "match_result": m,
                    "status": random.choice(["applied", "shortlisted", "interview"])})

        SavedJob.objects.filter(user=seeker).delete()
        for j in Job.objects.filter(source=Job.Source.DEMO, title__icontains="Python")[:3]:
            SavedJob.objects.create(user=seeker, job=j, status=random.choice(["saved", "applied", "interview"]))

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {n} demo jobs, {len(internal)} recruiter jobs, sample resume (ATS {res.ats_score}).\n"
            f"Logins ->  admin/{'admin123' if admin_pw == 'admin123' else '(ADMIN_PASSWORD)'}"
            "  |  recruiter/recruiter123  |  student/student123"))
