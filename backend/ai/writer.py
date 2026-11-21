"""
AI Resume Improver and Cover Letter generator.
Rule engine always works; Gemini (optional) writes more natural text.
"""
import re

from resumes.ml.analyzer import ACTION_VERBS
from resumes.ml.skill_extractor import technical_only
from resumes.ml.skills_db import SKILLS as SKILL_NAMES

from .llm import ask_json

WEAK = {
    r"^\s*(was\s+)?responsible for\s+": "Managed ",
    r"^\s*worked on\s+": "Developed ",
    r"^\s*helped (to\s+|with\s+)?": "Contributed to ",
    r"^\s*did\s+": "Completed ",
    r"^\s*made\s+": "Built ",
    r"^\s*handled\s+": "Managed ",
    r"^\s*involved in\s+": "Contributed to ",
    r"^\s*participated in\s+": "Took part in ",
    r"^\s*learned\s+": "Gained hands-on experience in ",
    r"^\s*used\s+": "Leveraged ",
}
NUMBER = re.compile(r"\d")


DATE_RANGE = re.compile(r"(19|20)\d{2}\s*(-|–|to)\s*((19|20)\d{2}|present|current|now)", re.I)
TITLE_WITH_STACK = re.compile(r"^[^.]{3,80}\([^)]*,[^)]*\)\s*$")   # "Project Name (Python, Django)"


def _is_heading(line):
    return bool(DATE_RANGE.search(line) or TITLE_WITH_STACK.match(line) or line.isupper()
                or (len(line.split()) <= 6 and not line.endswith(".")))


def _bullets(text):
    marked, plain = [], []
    for line in text.splitlines():
        raw = line.strip()
        clean = re.sub(r"^[\s•\-\*–·▪●]+", "", raw).strip()
        if not (25 <= len(clean) <= 220 and len(clean.split()) >= 5) or _is_heading(clean):
            continue
        (marked if raw[:1] in "•-*–·▪●" else plain).append(clean)
    return marked or plain    # prefer real bullet points


def _rule_improve_line(line):
    new, why = line, []
    for pat, rep in WEAK.items():
        if re.search(pat, new, re.I):
            new = re.sub(pat, rep, new, count=1, flags=re.I)
            why.append("Replaced a weak phrase with a strong action verb")
            break
    first_word = new.split()[0] if new.split() else ""
    first = first_word.lower().strip(",.")
    if not why and first not in ACTION_VERBS:
        keep_case = first_word[1:2].isupper() or first_word.lower() in {s.lower() for s in SKILL_NAMES}
        new = "Developed " + (new if keep_case else new[0].lower() + new[1:])
        why.append("Started with an action verb")
    if not NUMBER.search(new):
        new = new.rstrip(".") + ", improving [result] by [X]%."
        why.append("Add a number to show impact (replace [X] with your real figure)")
    elif not new.endswith("."):
        new += "."
    return new, why


def improve_resume(resume, max_items=8):
    sections = {}
    text = resume.raw_text or ""
    for name in ("experience", "projects"):
        m = re.search(rf"(?ims)^\s*{name}\s*$(.+?)(^\s*[A-Z][A-Z &]{{3,}}\s*$|\Z)", text)
        if m:
            sections[name] = m.group(1)
    source = "\n".join(sections.values()) or text
    lines = _bullets(source)
    weak = []
    for ln in lines:
        first = ln.split()[0].lower().strip(",.")
        if first not in ACTION_VERBS or not NUMBER.search(ln) or re.search("|".join(WEAK), ln, re.I):
            weak.append(ln)
    weak = weak[:max_items]
    skills = technical_only(resume.skills)[:8]
    role = resume.predicted_roles[0]["role"] if resume.predicted_roles else "Software Developer"

    data = ask_json(
        f"Improve these resume bullet points for a {role} (fresher / junior, India). Keep facts the same, start "
        "with strong action verbs, keep each under 30 words, and where there is no number add a placeholder like "
        "[X%] for the candidate to fill. Also write a 2-3 sentence professional summary.\n"
        f"Skills: {', '.join(skills)}. Experience: {resume.experience_years} years.\n"
        f"Bullets: {weak}\n"
        'Return JSON: {"summary":"...","items":[{"original":"...","improved":"...","why":"..."}]}'
    ) if weak else None

    items = []
    try:
        for it in data["items"]:
            if it.get("original") and it.get("improved"):
                items.append({"original": it["original"], "improved": it["improved"], "why": [str(it.get("why", ""))]})
        summary = str(data["summary"])
    except Exception:
        items = []
        for ln in weak:
            new, why = _rule_improve_line(ln)
            items.append({"original": ln, "improved": new, "why": why})
        yrs = resume.experience_years
        exp = f"{yrs:g}+ years of hands-on experience" if yrs >= 1 else "hands-on project and internship experience"
        summary = (f"{role} with {exp} in {', '.join(skills[:4]) or 'software development'}. "
                   f"Skilled in building practical, well-tested solutions{' with ' + ', '.join(skills[4:7]) if len(skills) > 4 else ''}. "
                   "Eager to contribute to a fast-growing team and keep learning new technologies.")
    return {"summary": summary, "items": items, "role": role, "checked_lines": len(lines)}


def cover_letter(resume, user, job_title, company, description="", tone="professional"):
    from resumes.ml.matcher import match_one
    m = match_one(resume.raw_text, resume.skills, resume.experience_years,
                  f"{job_title}\n{description}") if description else {"matched_skills": [], "missing_skills": []}
    name = resume.candidate_name or user.get_full_name() or user.username
    matched = m["matched_skills"][:5] or technical_only(resume.skills)[:5]
    data = ask_json(
        f"Write a {tone} cover letter (180-230 words) for {name} applying for '{job_title}' at '{company}'.\n"
        f"Candidate skills: {', '.join(resume.skills[:15])}. Experience: {resume.experience_years} years. "
        f"Education: {', '.join(resume.education)}.\nSkills matching the job: {', '.join(matched)}.\n"
        f"Job description: {description[:1500]}\nResume extract: {resume.raw_text[:1500]}\n"
        "Do not invent companies or numbers that are not in the resume. Plain text, no placeholders except the date.\n"
        'Return JSON: {"letter":"..."}', 1200)
    try:
        letter = str(data["letter"]).strip()
        if len(letter) > 200:
            return {"letter": letter, "matched_skills": matched}
    except Exception:
        pass

    edu = resume.education[0] if resume.education else "my degree"
    opener = {"professional": "I am writing to apply for", "enthusiastic": "I am excited to apply for",
              "confident": "I am confident I would be a strong fit for"}.get(tone, "I am writing to apply for")
    exp_line = (f"With {resume.experience_years:g} years of experience" if resume.experience_years >= 1
                else "Through my internship and academic projects")
    letter = f"""Dear Hiring Manager,

{opener} the {job_title} position at {company}. As a {edu} graduate with a strong interest in building real-world software, I believe my skills match what your team is looking for.

{exp_line}, I have worked with {', '.join(matched[:-1]) + ' and ' + matched[-1] if len(matched) > 1 else (matched[0] if matched else 'modern technologies')}. I enjoy turning requirements into clean, reliable solutions, and I always focus on writing maintainable code and learning quickly from feedback.

What attracts me to {company} is the opportunity to work on meaningful products with an experienced team. I am confident that my technical foundation, problem-solving mindset and willingness to learn will help me contribute from day one.

Thank you for considering my application. I would welcome the opportunity to discuss how I can add value to {company}.

Sincerely,
{name}
{resume.email or user.email}{(' | ' + resume.phone) if resume.phone else ''}"""
    return {"letter": letter, "matched_skills": matched}
