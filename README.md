# 🎯 JobMatch AI: AI-Powered Resume Analyzer with Real-Time Job Recommendations
### (ATS Score • Role-wise ATS • Live Jobs • AI Mock Interview • AI Resume Writer)

> **MCA Project** | Python • Django REST Framework • React • PostgreSQL • Redis • Celery • Machine Learning (NLP)

JobMatch AI reads a resume (PDF/DOCX), extracts information using NLP, gives an **ATS score with improvement tips**,
predicts the **best-fit job roles**, fetches **live job openings from the internet** (Adzuna / JSearch → LinkedIn, Indeed, Glassdoor),
and ranks every job by an **AI match percentage** with a **skill-gap analysis**.
Recruiters can post jobs and see applicants **automatically ranked by AI**.

---

## ✨ Features

| Module | Features |
|---|---|
| 👤 **Authentication** | JWT login (username or email), public sign-up for job seekers, role-based access, profile, change password |
| 📄 **Resume Analyzer (AI/NLP)** | PDF/DOCX/TXT parsing, extracts name, email, phone, LinkedIn, GitHub, education, years of experience, sections, 120+ skills in 15 categories |
| 📊 **ATS Score** | 0-100 score across 7 criteria (contact, links, sections, skills, action verbs, measurable achievements, length) + prioritised tips |
| 🎯 **Role-wise ATS Score** | The same resume is scored separately for each of 22 roles (Full Stack, Data Analyst, DevOps, Technical Support, IT Helpdesk, Customer Support, Business Analyst...): must-have skills (45), good-to-have skills (15), role keywords (15), title match (10), resume quality (15), with role-specific tips and a "roles you fit best" ranking |
| 🎯 **Role Prediction** | Predicts top-3 suitable roles (Python Dev, Full Stack, Data Scientist, …) with the core skills still missing |
| 🔴 **Live Job Recommendations** | Real-time jobs from 5 sources fetched **in parallel** (Remotive, Jobicy, Arbeitnow, Adzuna, JSearch), cached (6h), stored in PostgreSQL, ranked by AI match %, Apply opens the original job post |
| 🧠 **AI Match Engine** | `60% skill overlap + 30% semantic similarity (TF-IDF or BERT embeddings) + 10% experience fit` |
| ⚠️ **Skill Gap Analysis** | Matched vs missing skills for every job, with "learn this skill" links |
| 📝 **JD Matcher** | Paste any job description (from LinkedIn/Naukri) → instant match report + history |
| 📌 **Job Tracker** | Kanban board (Saved → Applied → Interview → Offer → Rejected), drag & drop |
| 🏢 **Recruiter Panel** | Post/edit/close jobs (skills auto-detected by AI), applicants ranked by AI score, shortlist/interview/hire workflow |
| 🛡️ **Admin Panel** | Platform analytics (signups, users by role, skill demand vs supply, ATS distribution), manage users, email test, Django admin at `/django-admin/` |
| ⏰ **Background Jobs** | **Celery + Redis**: resume processing, live-job refresh every 6h, daily email job alerts |
| 📈 **Dashboards** | Charts for seekers, recruiters and admins (Recharts) |
| 🗺️ **Skill Roadmap** | Pick a target role → week-by-week plan for missing skills, mini projects, free course links, "mark learned" progress and job-readiness % |
| 📱 **Installable app (PWA)** | Install on Android / desktop like an app (manifest + service worker, offline page) |
| 🌙 **Dark mode** | One-click light / dark theme, remembers your choice |
| 🔐 **Forgot password (email OTP)** | 6-digit code by email (hashed, 10-minute expiry, 5 attempts, 60-second resend limit) via Brevo API or Gmail SMTP; admin can send a test email and set a new password |
| 👥 **Access control** | Public sign-up creates job seekers only; recruiter accounts are created by the admin |
| 🤖 **AI Mock Interview** | Role / job based HR + technical + behavioural questions, instant score (0-10), strengths, improvements and key points for every answer, final verdict and history |
| ✍️ **AI Resume Improver** | Finds weak bullet points and rewrites them with action verbs and measurable impact; suggests a professional summary |
| 📝 **AI Cover Letter** | One-click, job-specific cover letter (3 tones), editable, copy / download, history |

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, React Router, Axios, Recharts, Lucide icons |
| Backend | Python 3.11+, Django 5, Django REST Framework, SimpleJWT |
| Database | PostgreSQL |
| Cache / Queue | Redis, Celery (worker + beat) |
| AI / ML | Scikit-learn (TF-IDF, cosine similarity), rule-based NER skill extraction, optional Sentence-Transformers (BERT) |
| Parsing | PyMuPDF, pdfplumber, python-docx |
| Job APIs | Remotive, Jobicy, Arbeitnow (no key) • Adzuna, JSearch (free key) |
| DevOps | Docker, Docker Compose, Gunicorn, WhiteNoise, Render + Neon |

---

## 🚀 How to Run

### Option A: Docker (easiest, one command)
```bash
docker compose up --build
```
Open **http://localhost:5173**. Demo data is loaded automatically.

### Option B: Manual setup (Windows / Linux / Mac)

**Requirements:** Python 3.11+, Node.js 18+, PostgreSQL 14+, Redis (optional but recommended)

#### 1. Create database
Open pgAdmin or psql and run:
```sql
CREATE DATABASE resume_ai;
```

#### 2. Backend
```bash
cd backend
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

copy .env.example .env        # Windows   (Linux/Mac: cp .env.example .env)
# -> open .env and set DB_PASSWORD to your PostgreSQL password

python manage.py migrate
python manage.py seed_demo     # demo users + 40 demo jobs + sample resume
python manage.py runserver
```
Backend runs at **http://localhost:8000** (Django admin at `/django-admin/`).

> 💡 No PostgreSQL installed yet? Set `DB_ENGINE=sqlite` in `.env` to test quickly.
> 💡 No Redis? Set `USE_REDIS=False` and keep `ASYNC_PROCESSING=False`. Everything still works.

#### 3. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173**

#### 4. (Optional) Celery for background jobs (new terminals, Redis must be running)
```bash
cd backend
celery -A config worker -l info          # on Windows add:  --pool=solo
celery -A config beat -l info            # schedules: refresh jobs every 6h, daily alerts
```
Set `ASYNC_PROCESSING=True` in `.env` to analyse resumes in the background worker.

### 🔑 Demo logins
| Role | Username | Password |
|---|---|---|
| Job Seeker | `student` | `student123` |
| Recruiter | `recruiter` | `recruiter123` |
| Admin | `admin` | `admin123` |

Sample resumes to upload are in the **`sample_resumes/`** folder.

---

## 🌍 Deploy online (free): see **[DEPLOY.md](DEPLOY.md)**
Render (website + API, one URL) + Neon (PostgreSQL). Step-by-step guide included.

---

## 🤖 Generative AI (optional)
All AI features work **without any key** using the built-in rule engine. For richer AI answers add a free
Google Gemini key (https://aistudio.google.com/apikey) as `GEMINI_API_KEY` in `.env` / Render Environment.
`GEMINI_MODEL` lets you change the model name if Google renames it. If Gemini fails, the app falls back to the rule engine automatically.

## 📧 Email setup (Forgot password)
Users get a **6-digit code by email**. Choose one provider:

**A) Laptop: Gmail App Password (5 minutes)**
1. Turn on **2-Step Verification** on your Google account: https://myaccount.google.com/security
2. Open https://myaccount.google.com/apppasswords → name it `JobMatch` → **Create** → copy the 16-letter password
3. In `backend/.env` add:
```
EMAIL_HOST_USER=yourname@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
```
4. Restart `python manage.py runserver`

**B) Live website on Render: Brevo (free, 300 emails/day)**. Render's free plan blocks SMTP, so Gmail SMTP won't work there.
1. Sign up at https://www.brevo.com
2. **Senders, Domains & Dedicated IPs → Senders → Add a sender** → your Gmail → open the verification mail
3. **SMTP & API → API Keys → Generate a new API key** → copy it
4. Render → your service → **Environment**: `BREVO_API_KEY` = the key, `EMAIL_FROM_ADDRESS` = the verified Gmail

**Check it:** log in as admin → **Users** → "Email for Forgot password" card → **Send test**. If it fails, the card shows the exact reason.
Without any provider: on the laptop (DEBUG=True) the code is shown on the page and printed in the terminal; on the live site users see a clear "contact admin" message and the admin can reset passwords with 🔑.

---

## 📧 Email (forgot password & job alerts)
Render's free plan blocks SMTP ports, so emails are sent with the **Brevo** HTTP API (free plan):
1. Sign up at https://www.brevo.com → **Senders** → add and verify your Gmail as a sender
2. **SMTP & API → API keys** → create a key
3. Add to Render Environment: `BREVO_API_KEY`, `EMAIL_FROM_ADDRESS` (your verified Gmail), `EMAIL_FROM_NAME=JobMatch AI`
Without a key, emails are printed in the server logs and the admin can reset passwords from **Admin → Users → 🔑**.

---

## 🔴 Real live jobs

**Works out of the box (no key):** Remotive, Jobicy and Arbeitnow (real remote jobs). The **Apply** button opens the
original job post. Sample/demo jobs are hidden automatically whenever real jobs are found.

**For India city jobs (Pune, Mumbai…), add a free Adzuna key:**

1. Register free at **https://developer.adzuna.com** and copy your **App ID** and **App Key**.
2. Put them in `backend/.env`:
   ```
   ADZUNA_APP_ID=your_id
   ADZUNA_APP_KEY=your_key
   ADZUNA_COUNTRY=in
   ```
3. Restart the backend and open **Live Jobs For You** → click **Refresh live feed**.

*Optional:* add `JSEARCH_API_KEY` (RapidAPI → JSearch) for LinkedIn/Indeed/Glassdoor jobs.
Results are cached in Redis for 6 hours so the free API limits are respected.

### 🧠 Optional: better AI matching (BERT embeddings)
```bash
pip install -r requirements-ai.txt
```
The matcher automatically switches from TF-IDF to Sentence-Transformers (`all-MiniLM-L6-v2`).
The engine in use is shown on the Live Jobs page.

---

## 🏗️ System Architecture

```
┌──────────────┐  JWT / REST   ┌──────────────────────────── Django REST API ─────────────────────────┐
│  React (Vite)│ ────────────► │ accounts │ resumes (AI pipeline) │ jobs (recommender) │ analytics     │
└──────────────┘               └────┬───────────────┬──────────────────────┬──────────────────────────┘
                                    │               │                      │
                              PostgreSQL       Redis cache ◄──── Adzuna / JSearch APIs (live jobs)
                                    ▲               │
                                    └──── Celery worker + beat (resume processing, job refresh, email alerts)
```

### AI pipeline (resume → recommendations)
```
Upload PDF/DOCX
   → Text extraction (PyMuPDF / pdfplumber / python-docx)
   → Cleaning + section detection (Summary, Skills, Experience, Education, Projects…)
   → Information extraction (regex NER: email, phone, links, degrees, experience date-ranges)
   → Skill extraction (gazetteer of 120+ skills & aliases, overlap-aware, ambiguity handling for C/R/Go)
   → ATS scoring (7 weighted criteria) + improvement tips
   → Role prediction (weighted core/bonus skill overlap)
   → Live job fetch for top role (Adzuna/JSearch → Redis cache → PostgreSQL)
   → Match scoring for every job:
        score = 0.6 × skill_overlap + 0.3 × semantic_similarity + 0.1 × experience_fit
   → Ranked jobs + matched/missing skills
```

---

## 🗄️ Database Design (PostgreSQL)

| Table | Important columns |
|---|---|
| `accounts_user` | id, username, email, password, **role** (seeker/recruiter/admin), phone, location, company_name, job_alerts_enabled |
| `resumes_resume` | id, user_id (FK), file, status, raw_text, candidate_name, email, phone, links (JSON), **skills (JSON)**, skills_by_category (JSON), education (JSON), experience_years, **ats_score**, analysis (JSON), predicted_roles (JSON), is_primary |
| `resumes_jdmatch` | id, user_id, resume_id, job_title, job_description, score, result (JSON) |
| `jobs_job` | id, **source** (internal/adzuna/jsearch/demo), external_id, title, company, location, description, skills (JSON), job_type, work_mode, min_experience, salary_min, salary_max, apply_url, posted_by (FK), is_active |
| `jobs_application` | id, job_id, seeker_id, resume_id, **match_score**, match_result (JSON), status, cover_note |
| `jobs_savedjob` | id, user_id, job_id, status (saved/applied/interview/offer/rejected), match_score, notes |
| `jobs_jobalertlog` | id, user_id, job_id, score, sent_at |

**Relations:** User 1-N Resume • User(recruiter) 1-N Job • Job 1-N Application N-1 User(seeker) • User 1-N SavedJob

---

## 🔌 Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` • `/api/auth/login/` | Register / login (JWT) |
| GET/PATCH | `/api/auth/me/` | Profile |
| GET/POST | `/api/resumes/` | List / upload resume (AI analysis) |
| GET | `/api/resumes/{id}/` | Full AI report |
| POST | `/api/resumes/match-jd/` | Match resume with pasted JD |
| GET | `/api/jobs/live/?q=&location=&job_type=&work_mode=&min_score=&refresh=1` | **Real-time recommended jobs** |
| GET/POST | `/api/jobs/` | Browse / post jobs |
| POST | `/api/jobs/{id}/apply/` | Apply (AI score saved) |
| GET | `/api/jobs/{id}/applicants/` | Recruiter: AI-ranked applicants |
| PATCH | `/api/jobs/applications/{id}/` | Update application status |
| CRUD | `/api/jobs/saved/` | Job tracker |
| GET | `/api/analytics/seeker/` • `/recruiter/` • `/admin/` • `/market/` | Dashboards |

---

## 🧪 Tests
```bash
cd backend
python manage.py test
```
11 tests: skill extraction, parsing, ATS analysis, matching, all 5 job-provider parsers (mocked), demo-job hiding,
offline fallback, resume download from DB, JD match and role permissions.

---

## 📁 Folder Structure
```
ai-resume-job-matcher/
├── backend/
│   ├── config/            settings, urls, celery
│   ├── accounts/          custom User (roles), JWT auth, permissions
│   ├── resumes/
│   │   ├── ml/            parser.py, skill_extractor.py, skills_db.py, analyzer.py, matcher.py, roles.py
│   │   ├── services.py    AI pipeline
│   │   └── tasks.py       Celery task
│   ├── jobs/
│   │   ├── services/      providers.py (5 job APIs), recommender.py
│   │   ├── tasks.py       refresh live jobs, email alerts
│   │   └── management/commands/seed_demo.py
│   ├── analytics/         dashboard APIs
│   ├── ai/                llm.py (Gemini, optional), interview.py, writer.py (improver + cover letter)
│   └── requirements.txt
├── frontend/src/
│   ├── pages/seeker/      Dashboard, Resume, LiveJobs, JDMatch, Tracker, Applications,
│   │                      Roadmap, Interview, AIWriter
│   ├── pages/recruiter/   Dashboard, Jobs, JobForm, Applicants
│   ├── pages/admin/       Dashboard, Users
│   └── components/        Layout, JobCard, JobModal, ui
├── sample_resumes/
├── Dockerfile             production image (React build + Django, one URL)
├── render.yaml            one-click Render deploy
├── DEPLOY.md              go-live guide
└── docker-compose.yml     local full stack (Postgres, Redis, Celery)
```

---

## 🔮 Future Scope
- OCR for scanned resumes (Tesseract)
- LLM-based resume rewriting suggestions
- Interview question generator for each job
- Mobile app (React Native)
- Salary prediction model

---

## 🛠️ Troubleshooting
| Problem | Fix |
|---|---|
| `password authentication failed for user "postgres"` | Set the correct `DB_PASSWORD` in `backend/.env` |
| `psycopg2` install error on Windows | `pip install psycopg2-binary --upgrade` |
| Redis connection errors | Start Redis, or set `USE_REDIS=False` in `.env` |
| Celery on Windows not running tasks | Use `celery -A config worker -l info --pool=solo` |
| Frontend shows network error | Make sure backend is running on port 8000 |
| Scanned (image) PDF fails | Upload a text-based PDF or DOCX |
