"""
Resume quality analyzer -> ATS-style score (0-100) + improvement tips.
"""
import re

from .skill_extractor import technical_only

ACTION_VERBS = {
    "developed", "built", "designed", "implemented", "created", "led", "managed", "optimized",
    "improved", "increased", "reduced", "automated", "deployed", "launched", "architected",
    "collaborated", "analyzed", "delivered", "integrated", "migrated", "mentored", "achieved",
    "engineered", "maintained", "streamlined", "resolved", "trained", "organized", "spearheaded",
}


def analyze_resume(parsed: dict, skills: list) -> dict:
    text = parsed["text"]
    low = text.lower()
    sections = parsed["sections"]
    tech = technical_only(skills)
    breakdown, tips = {}, []

    def tip(priority, title, detail):
        tips.append({"priority": priority, "title": title, "detail": detail})

    # 1. Contact (10)
    c = (5 if parsed["email"] else 0) + (5 if parsed["phone"] else 0)
    breakdown["Contact Info"] = (c, 10)
    if not parsed["email"]:
        tip("high", "Add your email", "Recruiters and ATS systems need a professional email address at the top.")
    if not parsed["phone"]:
        tip("high", "Add your phone number", "Include a 10-digit mobile number with country code (+91).")

    # 2. Online presence (5)
    links = parsed["links"]
    l = (3 if links.get("linkedin") else 0) + (2 if links.get("github") else 0)
    breakdown["LinkedIn / GitHub"] = (l, 5)
    if not links.get("linkedin"):
        tip("medium", "Add LinkedIn profile", "A LinkedIn URL increases recruiter trust and response rate.")
    if not links.get("github") and len(tech) > 2:
        tip("medium", "Add GitHub profile", "For tech roles, a GitHub link with your projects is a big plus.")

    # 3. Sections (40)
    weights = {"summary": 5, "skills": 10, "experience": 10, "education": 8, "projects": 7}
    s_score = 0
    for sec, w in weights.items():
        if sec in sections:
            s_score += w
        else:
            msg = {
                "summary": ("Add a Professional Summary", "Write 2-3 lines about who you are, your key skills and the role you want."),
                "skills": ("Add a dedicated Skills section", "List technical skills clearly (e.g. Python, React, PostgreSQL) so ATS can read them."),
                "experience": ("Add Experience / Internship section", "Even internships, freelance or college projects count as experience."),
                "education": ("Add Education section", "Mention degree, college, year and percentage/CGPA."),
                "projects": ("Add a Projects section", "Show 2-3 projects with tech stack and what you achieved."),
            }[sec]
            tip("high" if sec in ("skills", "education") else "medium", *msg)
    breakdown["Resume Sections"] = (s_score, 40)

    # 4. Technical skills (15)
    k = min(15, round(len(tech) * 15 / 10))
    breakdown["Technical Skills"] = (k, 15)
    if len(tech) < 6:
        tip("high", "Add more relevant technical skills",
            f"Only {len(tech)} technical skills detected. Aim for 8-15 skills relevant to your target role.")

    # 5. Action verbs (10)
    words = set(re.findall(r"[a-z]+", low))
    verbs = words & ACTION_VERBS
    v = min(10, len(verbs) * 2)
    breakdown["Action Verbs"] = (v, 10)
    if len(verbs) < 4:
        tip("medium", "Use strong action verbs",
            "Start bullet points with words like Developed, Built, Optimized, Led, Automated.")

    # 6. Quantified achievements (10)
    quant = re.findall(r"\b\d+(?:\.\d+)?\s?(?:%|\+|x\b|k\b|lakh|users|clients|projects|ms\b)", low)
    q = min(10, len(quant) * 3)
    breakdown["Measurable Achievements"] = (q, 10)
    if len(quant) < 2:
        tip("medium", "Add numbers to your achievements",
            "e.g. 'Reduced API response time by 40%' or 'Built app used by 500+ students'.")

    # 7. Length (10)
    wc = parsed["word_count"]
    if 300 <= wc <= 900:
        ln = 10
    elif 200 <= wc < 300 or 900 < wc <= 1200:
        ln = 6
    else:
        ln = 2
    breakdown["Length"] = (ln, 10)
    if wc < 300:
        tip("medium", "Resume is too short", f"Your resume has ~{wc} words. Aim for 400-800 words (1 page for freshers).")
    elif wc > 1200:
        tip("low", "Resume is too long", f"~{wc} words. Keep it to 1-2 pages; remove old or irrelevant details.")

    total = sum(v[0] for v in breakdown.values())
    if total >= 80:
        grade = "Excellent"
    elif total >= 65:
        grade = "Good"
    elif total >= 45:
        grade = "Average"
    else:
        grade = "Needs Work"

    order = {"high": 0, "medium": 1, "low": 2}
    tips.sort(key=lambda t: order[t["priority"]])
    return {
        "score": total,
        "grade": grade,
        "breakdown": [{"label": k, "score": v[0], "max": v[1]} for k, v in breakdown.items()],
        "tips": tips,
        "action_verbs_found": sorted(verbs),
    }
