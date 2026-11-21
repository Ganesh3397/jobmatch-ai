"""
Role-specific ATS score.

The same resume gets a different score for "Full Stack Developer" and for
"Technical Support Engineer", because each role is checked against its own
must-have skills, good-to-have skills and role keywords.

role_score (0-100) =
    45  must-have (core) skills found
  + 15  good-to-have (bonus) skills found
  + 15  role keywords used in the resume text
  + 10  role title / summary alignment
  + 15  general resume quality (the normal ATS score)
"""
import re

from .roles import ROLES
from .skill_extractor import extract_skills

GROUPS = {
    "Development": ["Python Developer", "Full Stack Developer", "Frontend Developer", "Backend Developer", "Java Developer"],
    "Data & AI": ["Data Analyst", "Data Scientist", "Machine Learning Engineer", "AI / GenAI Engineer", "Business Analyst"],
    "Cloud, Infra & Security": ["DevOps Engineer", "Cloud Engineer", "Database Administrator", "Network Engineer",
                                "Cyber Security Analyst"],
    "Mobile & Design": ["Android Developer", "Mobile App Developer", "UI/UX Designer"],
    "Testing": ["QA / Test Engineer"],
    "Support": ["Technical Support Engineer", "IT Support / Helpdesk", "Customer Support Executive"],
}

# words recruiters / ATS look for in the experience & project text of each role
KEYWORDS = {
    "Python Developer": ["python", "api", "automation", "script", "backend", "django", "database"],
    "Full Stack Developer": ["frontend", "backend", "full stack", "api", "deploy", "responsive", "database", "authentication"],
    "Frontend Developer": ["responsive", "ui", "component", "accessibility", "cross-browser", "performance", "frontend"],
    "Backend Developer": ["api", "database", "server", "authentication", "scalable", "microservice", "backend", "cache"],
    "Java Developer": ["java", "spring", "api", "oop", "microservice", "backend", "jdbc"],
    "Data Analyst": ["dashboard", "report", "insight", "kpi", "visualize", "analysis", "query", "trend"],
    "Data Scientist": ["model", "prediction", "dataset", "feature", "accuracy", "machine learning", "statistics"],
    "Machine Learning Engineer": ["model", "training", "deploy", "pipeline", "accuracy", "inference", "dataset"],
    "AI / GenAI Engineer": ["llm", "prompt", "rag", "embedding", "chatbot", "generative", "agent"],
    "Business Analyst": ["requirement", "stakeholder", "process", "report", "documentation", "user stories", "workflow"],
    "DevOps Engineer": ["pipeline", "deploy", "automation", "container", "monitoring", "infrastructure", "ci/cd"],
    "Cloud Engineer": ["cloud", "ec2", "s3", "deploy", "scalable", "infrastructure", "serverless"],
    "Database Administrator": ["database", "backup", "query", "performance tuning", "index", "replication", "recovery"],
    "Network Engineer": ["network", "router", "switch", "tcp/ip", "lan", "firewall", "vpn"],
    "Cyber Security Analyst": ["security", "vulnerability", "firewall", "threat", "incident", "penetration", "malware"],
    "Android Developer": ["app", "android", "play store", "ui", "api", "kotlin", "mobile"],
    "Mobile App Developer": ["app", "mobile", "android", "ios", "play store", "ui", "api"],
    "UI/UX Designer": ["wireframe", "prototype", "user research", "design", "usability", "persona", "figma"],
    "QA / Test Engineer": ["test case", "bug", "automation", "regression", "test plan", "defect", "testing"],
    "Technical Support Engineer": ["ticket", "troubleshoot", "customer", "resolve", "issue", "sla", "escalate", "install"],
    "IT Support / Helpdesk": ["desktop", "hardware", "printer", "install", "user", "ticket", "network", "windows"],
    "Customer Support Executive": ["customer", "query", "resolve", "call", "email", "chat", "satisfaction", "escalate"],
}

TITLES = {
    "Technical Support Engineer": ["support engineer", "technical support", "tech support", "application support"],
    "IT Support / Helpdesk": ["it support", "helpdesk", "help desk", "desktop support", "system support"],
    "Customer Support Executive": ["customer support", "customer service", "support executive", "customer care"],
    "QA / Test Engineer": ["qa", "tester", "test engineer", "quality assurance"],
    "AI / GenAI Engineer": ["ai engineer", "genai", "generative ai"],
    "UI/UX Designer": ["ui/ux", "ux designer", "ui designer", "product designer"],
}


def all_roles():
    return list(ROLES.keys())


def _has(text, kw):
    """'resolve' also matches resolved / resolving, 'scalable' matches scalability (simple stemming)."""
    stem = kw if len(kw) <= 5 else kw[:-2]
    return re.search(r"(?<![a-z])" + re.escape(stem), text) is not None


def role_ats(resume, role):
    core, bonus = ROLES[role]
    text = (resume.raw_text or "").lower()
    have = {s.lower() for s in resume.skills}
    have |= {s.lower() for s in extract_skills(resume.raw_text or "")["skills"]}   # also new skill types

    core_hit = [s for s in core if s.lower() in have]
    bonus_hit = [s for s in bonus if s.lower() in have]
    kws = KEYWORDS.get(role, [])
    kw_hit = [k for k in kws if _has(text, k)]
    titles = TITLES.get(role, [role.lower().split("/")[0].strip(), role.lower().replace(" developer", "").strip()])
    title_hit = any(_has(text, t) for t in titles)

    parts = {
        "Must-have skills": (len(core_hit) / len(core) * 45) if core else 45,
        "Good-to-have skills": (len(bonus_hit) / len(bonus) * 15) if bonus else 15,
        "Role keywords": (min(1.0, len(kw_hit) / max(1, round(len(kws) * 0.6))) * 15) if kws else 15,
        "Role title match": 10 if title_hit else 0,
        "Resume quality": resume.ats_score / 100 * 15,
    }
    maxes = {"Must-have skills": 45, "Good-to-have skills": 15, "Role keywords": 15, "Role title match": 10, "Resume quality": 15}
    score = round(sum(parts.values()))

    tips = []
    missing_core = [s for s in core if s not in core_hit]
    missing_bonus = [s for s in bonus if s not in bonus_hit]
    if missing_core:
        tips.append({"priority": "high", "title": f"Add must-have skills for {role}",
                     "detail": f"If you know {', '.join(missing_core)}, list them in your Skills section and show them in a project or internship."})
    kw_miss = [k for k in kws if k not in kw_hit]
    if len(kw_hit) < max(1, round(len(kws) * 0.6)):
        tips.append({"priority": "medium", "title": "Use role keywords in your experience",
                     "detail": f"ATS for {role} looks for words like: {', '.join(kw_miss[:6])}. Use them naturally in your bullet points."})
    if not title_hit:
        tips.append({"priority": "medium", "title": "Mention the role in your summary",
                     "detail": f"Write a 1-2 line summary that includes the title '{role}' so the ATS matches you to it."})
    if missing_bonus and len(bonus_hit) < len(bonus) / 2:
        tips.append({"priority": "low", "title": "Good-to-have skills",
                     "detail": f"Learning {', '.join(missing_bonus[:4])} will make you stand out for {role}."})
    if resume.ats_score < 65:
        tips.append({"priority": "medium", "title": "Improve overall resume quality",
                     "detail": "Your general ATS score is low. Check the improvement tips in the main ATS report above."})

    grade = "Excellent" if score >= 80 else "Good" if score >= 65 else "Average" if score >= 45 else "Low"
    return {
        "role": role, "score": score, "grade": grade,
        "breakdown": [{"label": k, "score": round(v), "max": maxes[k]} for k, v in parts.items()],
        "matched_core": core_hit, "missing_core": missing_core,
        "matched_bonus": bonus_hit, "missing_bonus": missing_bonus,
        "keywords_found": kw_hit, "keywords_missing": kw_miss,
        "title_match": title_hit, "tips": tips,
    }


def ranking(resume, top=6):
    rows = [{"role": r, "score": role_ats(resume, r)["score"]} for r in ROLES]
    return sorted(rows, key=lambda x: -x["score"])[:top]
