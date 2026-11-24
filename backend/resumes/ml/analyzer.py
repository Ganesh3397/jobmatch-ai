"""
Resume quality analyzer -> ATS-style score (0-100) + improvement tips.

Eight checks, 100 marks in total. The checks are deliberately strict so that
an average resume scores 50-70 and only a well-written, role-focused resume
reaches 85+ (a real ATS rarely gives 100).

    Contact details ............ 10
    Resume sections ............ 20
    Skills for best-fit role ... 20
    Number of relevant skills ..  5
    Action verbs ............... 10
    Measurable achievements .... 10
    Length ..................... 10
    Readability & formatting ... 15
"""
import re

from .roles import predict_roles, ROLES
from .skill_extractor import technical_only

# bump this when the scoring rules or skill list change -> "rescore_resumes" re-scores old resumes on deploy
RULES_VERSION = 3

ACTION_VERBS = {
    "developed", "built", "designed", "implemented", "created", "led", "managed", "optimized", "optimised",
    "improved", "increased", "reduced", "automated", "deployed", "launched", "architected",
    "collaborated", "analyzed", "analysed", "delivered", "integrated", "migrated", "mentored", "achieved",
    "engineered", "maintained", "streamlined", "resolved", "trained", "organized", "organised", "spearheaded",
    "negotiated", "generated", "prepared", "conducted", "coordinated", "handled", "processed", "reconciled",
    "supervised", "taught", "recruited", "executed", "planned", "established", "exceeded", "converted",
    "audited", "presented", "facilitated", "won", "earned", "secured", "boosted", "accelerated",
}
WEAK_PHRASES = ["responsible for", "worked on", "duties included", "helped with", "involved in",
                "tasks included", "assisted in"]
BULLET_RX = re.compile(r"^\s*(?:[•●▪◦‣\-\*–]|\d+[.)])\s+\S", re.M)
FIRST_PERSON_RX = re.compile(r"\b(?:i|me|my|myself)\b", re.I)
DATE_RX = re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*[-'’]?\s*\d{2,4}\b"
                     r"|\b(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:(?:19|20)\d{2}|present|current|now)\b", re.I)
QUANT_RX = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|\+|x\b|k\b|lakh|lakhs|crore|cr\b|users|clients|customers|students|"
                      r"projects|ms\b|hours|days|members|people|accounts|calls|leads|orders|sales|rs\b|inr\b)"
                      r"|(?:₹|rs\.?\s?|inr\s?)\d", re.I)


def _best_role(skills, text=""):
    roles = predict_roles(skills, top_n=1, text=text)
    return roles[0]["role"] if roles else None


def analyze_resume(parsed: dict, skills: list) -> dict:
    text = parsed["text"]
    low = text.lower()
    sections = parsed["sections"]
    domain = technical_only(skills)          # every skill except soft skills (works for IT and non-IT)
    breakdown, tips = {}, []

    def tip(priority, title, detail):
        tips.append({"priority": priority, "title": title, "detail": detail})

    # 1. Contact details (10)
    links = parsed["links"]
    c = (4 if parsed["email"] else 0) + (4 if parsed["phone"] else 0) + (2 if links.get("linkedin") else 0)
    breakdown["Contact Details"] = (c, 10)
    if not parsed["email"]:
        tip("high", "Add your email", "Recruiters and ATS systems need a professional email address at the top.")
    if not parsed["phone"]:
        tip("high", "Add your phone number", "Include a 10-digit mobile number with country code (+91).")
    if not links.get("linkedin"):
        tip("medium", "Add your LinkedIn profile", "A LinkedIn URL increases recruiter trust and response rate.")

    # 2. Sections (20)
    weights = {"summary": 4, "skills": 4, "experience": 5, "education": 4}
    s_score = sum(w for sec, w in weights.items() if sec in sections)
    if "projects" in sections or "certifications" in sections:
        s_score += 3
    breakdown["Resume Sections"] = (s_score, 20)
    msgs = {
        "summary": ("high", "Add a Professional Summary", "Write 2-3 lines about who you are, your key skills and the role you want."),
        "skills": ("high", "Add a dedicated Skills section", "List your key skills clearly so the ATS can read them."),
        "experience": ("medium", "Add Experience / Internship section", "Internships, part-time work, freelance work or projects all count."),
        "education": ("high", "Add Education section", "Mention degree, college, year and percentage/CGPA."),
    }
    for sec, (pr, t, d) in msgs.items():
        if sec not in sections:
            tip(pr, t, d)
    if "projects" not in sections and "certifications" not in sections:
        tip("medium", "Add Projects or Certifications", "Show 2-3 projects, certifications or achievements with what you did.")

    # 3. Skills for the best-fit role (20)
    role = _best_role(skills, text)
    have = {s.lower() for s in skills}
    if role:
        core, bonus = ROLES[role]
        core_hit = [s for s in core if s.lower() in have]
        bonus_hit = [s for s in bonus if s.lower() in have]
        rs = round(len(core_hit) / len(core) * 12 + (len(bonus_hit) / len(bonus) * 8 if bonus else 8))
        missing = [s for s in core + bonus if s.lower() not in have]
        if missing and rs < 16:
            tip("high" if rs < 10 else "medium", f"Add more skills for {role}",
                f"Recruiters for {role} also look for: {', '.join(missing[:5])}. Add the ones you know.")
    else:
        rs = min(6, len(domain))
        tip("high", "Mention clear job skills",
            "No clear job role could be detected. List the tools and skills of the job you want (e.g. Tally, GST, Sales, Python).")
    breakdown["Skills for Target Role"] = (rs, 20)

    # 4. Number of relevant skills (5)
    k = min(5, len(domain) // 2)
    breakdown["Number of Skills"] = (k, 5)
    if len(domain) < 6:
        tip("medium", "Add more relevant skills", f"Only {len(domain)} job skills detected. Aim for 8-15 skills relevant to your target role.")

    # 5. Action verbs (10)
    words = set(re.findall(r"[a-z]+", low))
    verbs = words & ACTION_VERBS
    weak = [p for p in WEAK_PHRASES if p in low]
    v = max(0, min(10, round(len(verbs) * 1.25)) - min(3, len(weak)))
    breakdown["Action Verbs"] = (v, 10)
    if len(verbs) < 6:
        tip("medium", "Use strong action verbs",
            "Start bullet points with words like Developed, Managed, Achieved, Reduced, Prepared, Led.")
    if weak:
        tip("medium", "Avoid weak phrases",
            f"Replace phrases like '{weak[0]}' with an action verb and a result, e.g. 'Managed 50+ client accounts'.")

    # 6. Measurable achievements (10)
    quant = QUANT_RX.findall(text)
    q = min(10, len(quant) * 2)
    breakdown["Measurable Achievements"] = (q, 10)
    if len(quant) < 4:
        tip("medium", "Add numbers to your achievements",
            "e.g. 'Reduced processing time by 40%', 'Handled 60+ customer calls daily' or 'Taught 120 students'.")

    # 7. Length (10)
    wc = parsed["word_count"]
    if 400 <= wc <= 800:
        ln = 10
    elif 300 <= wc < 400 or 800 < wc <= 1000:
        ln = 7
    elif 200 <= wc < 300 or 1000 < wc <= 1300:
        ln = 4
    else:
        ln = 1
    breakdown["Length"] = (ln, 10)
    if wc < 400:
        tip("medium", "Resume is too short", f"Your resume has ~{wc} words. Aim for 400-800 words (1 page for freshers).")
    elif wc > 1000:
        tip("low", "Resume is too long", f"~{wc} words. Keep it to 1-2 pages; remove old or irrelevant details.")

    # 8. Readability & formatting (15)
    bullets = len(BULLET_RX.findall(text))
    first_person = len(FIRST_PERSON_RX.findall(text))
    long_lines = sum(1 for line in text.splitlines() if len(line.split()) > 45)
    dates = len(DATE_RX.findall(text))
    f = (5 if bullets >= 5 else 3 if bullets >= 2 else 0) \
        + (4 if first_person <= 2 else 2 if first_person <= 5 else 0) \
        + (3 if long_lines == 0 else 1 if long_lines == 1 else 0) \
        + (3 if dates >= 2 else 1 if dates == 1 else 0)
    breakdown["Readability & Formatting"] = (f, 15)
    if bullets < 5:
        tip("medium", "Use bullet points", "Write experience and projects as short bullet points instead of paragraphs.")
    if first_person > 2:
        tip("low", "Avoid 'I', 'me', 'my'", "Resumes are written without first-person words: 'Managed accounts', not 'I managed accounts'.")
    if long_lines:
        tip("low", "Break long paragraphs", "Keep each line under 2 rows; ATS and recruiters skim quickly.")
    if dates < 2:
        tip("medium", "Add dates", "Add start and end dates (e.g. Jun 2024 - Present) to your experience and education.")

    total = sum(val[0] for val in breakdown.values())
    if total >= 85:
        grade = "Excellent"
    elif total >= 70:
        grade = "Good"
    elif total >= 50:
        grade = "Average"
    else:
        grade = "Needs Work"

    order = {"high": 0, "medium": 1, "low": 2}
    tips.sort(key=lambda t: order[t["priority"]])
    return {
        "score": total,
        "grade": grade,
        "best_role": role,
        "rules_version": RULES_VERSION,
        "breakdown": [{"label": key, "score": val[0], "max": val[1]} for key, val in breakdown.items()],
        "tips": tips,
        "action_verbs_found": sorted(verbs),
    }
