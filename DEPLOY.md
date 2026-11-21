# 🌍 Project LIVE kasa karaycha (free) — Render + Neon

Shevti tula ek link milel, udaharan **https://jobmatch-ai.onrender.com**.
Ti link WhatsApp status la thev. Friends ti ughadun **register karun sagla vapru shaktil**.

| Kaam | Service | Kharch |
|---|---|---|
| Website + Backend (Django + React ekach link var) | **Render** | Free |
| Database (PostgreSQL) | **Neon** | Free |
| Code thevayla | **GitHub** | Free |

> ⚠️ Free plan: 15 minute konich website vaparli nahi tar ti "sleep" hote.
> Nantar pahila user aala ki website ughdayla **~1 minute** lagto, mag fast chalte.

---

## Step 1: Code GitHub var tak

1. https://github.com var account banav ani login kar
2. Varti ujvya bajula **+** → **New repository** → naav `jobmatch-ai` → **Public** → **Create repository**
3. VS Code madhe project folder (`ai-resume-job-matcher`) ughad → **navin terminal** ughad (venv chi garaj nahi):

```powershell
git init
git add .
git commit -m "JobMatch AI - MCA project"
git branch -M main
git remote add origin https://github.com/TUJHA_USERNAME/jobmatch-ai.git
git push -u origin main
```
> `TUJHA_USERNAME` chya jagi tujha GitHub username lihi.
> Pahilyanda push kartana GitHub login cha popup yeil → **Sign in with browser**.
> `.env` file (tujha password) `.gitignore` mule GitHub var **janar nahi** ✅

---

## Step 2: Free database banav (Neon)

1. https://neon.com → **Sign up** (GitHub ne login kar)
2. **Create project** → naav `jobmatch` → Region: **AWS Asia Pacific (Singapore)** → Create
3. Dashboard var **Connect** button → **Connection string** copy kar. Ti ashi diste:
```
postgresql://neondb_owner:xxxxxxxx@ep-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```
👉 Hi string Notepad madhe thevun de (Step 3 madhe lagel).

---

## Step 3: Website deploy kar (Render)

1. https://render.com → **Get Started** → **GitHub ne sign up** kar
2. Dashboard → **+ New** → **Blueprint**
3. Tujhi `jobmatch-ai` repository **Connect** kar
4. Render `render.yaml` vachun setup dakhavel. Tithe he 2 values bhar:

| Key | Value |
|---|---|
| `DATABASE_URL` | Step 2 madhli Neon connection string |
| `ADMIN_PASSWORD` | admin login sathi tujha strong password (udaharan `Ganesh@2026`) |

> `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` rikame thevle tari chalel (India city jobs sathi nantar takta yetat).

5. **Apply / Deploy** dabav
6. ⏳ Pahila build **8-15 minute** gheto (React build + Python packages). **Logs** madhe shevti `Listening at: http://0.0.0.0:...` disla ki tayar ✅
7. Varti tujhi link disel: **https://jobmatch-ai-xxxx.onrender.com** 🎉

> Blueprint option disla nahi tar: **+ New → Web Service** → repo nivad → Language **Docker** →
> Instance **Free** → khali **Environment Variables** madhe `DATABASE_URL`, `ADMIN_PASSWORD`,
> `SECRET_KEY` (kahi pan lamba random text), `DEBUG=False`, `USE_REDIS=False` taak → **Deploy**.

---

## Step 4: Check kar

- Link ughad → **Create an account** → navin account banav → resume upload kar ✅
- Admin: username `admin` ani password = tu takleli `ADMIN_PASSWORD`
- Django admin panel: `https://tujhi-link.onrender.com/django-admin/`
- Demo logins pan chaltat: `student / student123`, `recruiter / recruiter123`

## Step 5: Share kar 📱
Link copy karun **WhatsApp status / Instagram story** la thev:
> "Majha MCA project live aahe 🚀 AI Resume Analyzer + Real-time Job Matching. Register karun try kara: https://..."

---

## 🔄 Code madhe badal kela tar website update kashi karaychi
```powershell
git add .
git commit -m "update"
git push
```
Render **automatic** navin version deploy karto (5-10 minute).
Database madhla data (users, resumes) **tasach rahto**. Demo data parat bharla jat nahi.

---

## 🔴 Live jobs
- **Remotive, Jobicy, Arbeitnow**: remote jobs, **key lagat nahi**, automatic chaltat
- **Pune/Mumbai/Bengaluru che jobs** pahije astil tar: https://developer.adzuna.com var free key ghe →
  Render → tujhi service → **Environment** → `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` taak → **Save** (auto redeploy)

---

## 🤖 (Optional) Gemini AI ani 📧 Email
Render → jobmatch-ai → **Environment** → **Add Environment Variable**:
| Key | Value |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey varun free key (AI interview / writer aankhi hushar hotat) |
| `BREVO_API_KEY` | brevo.com → SMTP & API → API Keys (forgot password cha code email ne jaycha sathi) |
| `EMAIL_FROM_ADDRESS` | Brevo → Senders madhe verify kelela tujha Gmail |
| `EMAIL_FROM_NAME` | `JobMatch AI` |
Save kela ki Render automatic restart karto. Mag admin login → **Users** → **Send test** ne email check kar.
⚠️ Render free plan var Gmail SMTP chalat nahi (port block), mhanun live sathi Brevo ch vapar. Steps README → *Email setup* madhe aahet.

## 🛠️ Problem aala tar
| Problem | Upay |
|---|---|
| Build fail | Render → **Logs** madhla shevtcha lal error copy karun pathav |
| `DisallowedHost` | Render var hi problem yet nahi (link automatic allow hote) |
| Database error | `DATABASE_URL` barobar copy zhali ka check kar (shevti `?sslmode=require` asava) |
| Website ughdayla vel lagto | Free plan sleep mule; 1 minute thamb |
| Admin login hot nahi | Render Environment madhe `ADMIN_PASSWORD` set aahe ka bagh. Database madhe users adhi pasun astil tar tyaivaji: Render → **Shell** → `python manage.py createsuperuser` |
