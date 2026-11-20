"""
Resume parser: PDF / DOCX / TXT  ->  clean text  ->  structured fields.
"""
import re
from datetime import date

SECTION_HEADINGS = {
    "summary": ["summary", "profile", "objective", "career objective", "about me", "professional summary"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "technologies", "tech stack", "skill set"],
    "experience": ["experience", "work experience", "professional experience", "employment history", "internship", "internships", "work history"],
    "education": ["education", "academic details", "academics", "qualification", "qualifications", "educational qualification"],
    "projects": ["projects", "academic projects", "personal projects", "key projects"],
    "certifications": ["certifications", "certificates", "courses", "achievements", "awards"],
}

DEGREES = [
    ("Ph.D", r"ph\.?\s?d"), ("M.Tech", r"m\.?\s?tech"), ("M.E", r"\bm\.e\.?\b"),
    ("MCA", r"\bmca\b|master of computer application"), ("MBA", r"\bmba\b"),
    ("M.Sc", r"m\.?\s?sc"), ("M.Com", r"m\.?\s?com\b"),
    ("B.Tech", r"b\.?\s?tech"), ("B.E", r"\bb\.e\.?\b|bachelor of engineering"),
    ("BCA", r"\bbca\b|bachelor of computer application"), ("B.Sc", r"b\.?\s?sc"),
    ("BBA", r"\bbba\b"), ("B.Com", r"b\.?\s?com\b"), ("Diploma", r"\bdiploma\b"),
    ("HSC", r"\bhsc\b|12th|xii"), ("SSC", r"\bssc\b|10th|\bx\b standard"),
]

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"


# ------------------------------------------------------------------ text extraction
def extract_text_from_bytes(data: bytes, filename: str) -> str:
    import os
    import tempfile
    suffix = os.path.splitext(filename)[1] or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        return extract_text(tmp_path)
    finally:
        os.remove(tmp_path)


def extract_text(path: str) -> str:
    p = path.lower()
    if p.endswith(".pdf"):
        return _pdf_text(path)
    if p.endswith(".docx"):
        return _docx_text(path)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _pdf_text(path):
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz  # older PyMuPDF
        with fitz.open(path) as doc:
            return "\n".join(page.get_text() for page in doc)
    except Exception:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join((pg.extract_text() or "") for pg in pdf.pages)


def _docx_text(path):
    try:
        import docx
        d = docx.Document(path)
        return "\n".join(p.text for p in d.paragraphs)
    except ImportError:
        import zipfile
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf8", "ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)


def clean_text(text: str) -> str:
    text = text.replace("•", "•").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


# ------------------------------------------------------------------ structure
def split_sections(text: str) -> dict:
    """Find section headings and return {section: content}."""
    lookup = {}
    for key, names in SECTION_HEADINGS.items():
        for n in names:
            lookup[n] = key
    sections, current = {"header": []}, "header"
    for line in text.splitlines():
        stripped = re.sub(r"[^a-zA-Z &]", "", line).strip().lower()
        if stripped in lookup and len(line.strip()) < 40:
            current = lookup[stripped]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def extract_email(text):
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return m.group(0) if m else ""


def extract_phone(text):
    for m in re.finditer(r"\+?\(?\d[\d\s().-]{8,18}\d", text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 13 and not re.match(r"^(19|20)\d{2}\D", m.group(0)):
            return m.group(0).strip()
    return ""


def extract_links(text):
    links = re.findall(r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com)/[\w\-/]+", text, re.I)
    return {
        "linkedin": next((l for l in links if "linkedin" in l.lower()), ""),
        "github": next((l for l in links if "github" in l.lower()), ""),
    }


def extract_name(text):
    for line in text.splitlines()[:8]:
        line = line.strip()
        if not line or "@" in line or re.search(r"\d", line):
            continue
        words = line.split()
        if 1 < len(words) <= 4 and all(re.match(r"^[A-Za-z.'-]+$", w) for w in words):
            if line.lower() not in sum(SECTION_HEADINGS.values(), []):
                return line.title() if line.isupper() else line
    return ""


def extract_education(text):
    low = text.lower()
    found = []
    for name, rx in DEGREES:
        if re.search(rx, low):
            found.append(name)
    return found


def extract_experience_years(text, experience_section=""):
    """Explicit 'X years' mention, else sum of date ranges in experience section."""
    explicit = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)", text, re.I)
    if explicit:
        return round(max(float(x) for x in explicit), 1)

    zone = experience_section or ""
    total_months = 0
    rx = re.compile(
        rf"(?:({MONTHS})[a-z]*\.?\s*)?(\d{{4}})\s*(?:-|–|to)\s*(?:(?:({MONTHS})[a-z]*\.?\s*)?(\d{{4}})|(present|current|now|till date))",
        re.I,
    )
    month_idx = {m: i + 1 for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
    for m in rx.finditer(zone):
        sm = month_idx.get((m.group(1) or "jan").lower()[:3], 1)
        sy = int(m.group(2))
        if m.group(5):
            ey, em = date.today().year, date.today().month
        else:
            ey = int(m.group(4))
            em = month_idx.get((m.group(3) or "dec").lower()[:3], 12)
        months = (ey - sy) * 12 + (em - sm)
        if 0 < months < 12 * 40:
            total_months += months
    return round(total_months / 12, 1)


def parse_resume_text(raw_text: str) -> dict:
    text = clean_text(raw_text)
    sections = split_sections(text)
    return {
        "text": text,
        "sections": sections,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "links": extract_links(text),
        "education": extract_education(sections.get("education", text)),
        "experience_years": extract_experience_years(text, sections.get("experience", "")),
        "word_count": len(text.split()),
    }
