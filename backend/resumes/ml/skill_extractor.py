"""
NLP based skill extraction.

Approach (rule-based NER with a skill gazetteer):
1. Normalise the text.
2. For every skill + alias in the taxonomy build a boundary-aware regex.
3. Short / ambiguous aliases (e.g. "C", "R", "Go", "ML") are only accepted
   inside list-like lines or a "Skills" section to avoid false positives.
4. Count frequency -> used as a confidence / weight.
"""
import re
from collections import Counter
from functools import lru_cache

from .skills_db import AMBIGUOUS_ALIASES, SKILLS, SOFT_SKILL_CATEGORY, category_of

_BOUND_L = r"(?<![A-Za-z0-9+#.])"
_BOUND_R = r"(?![A-Za-z0-9+#])"


def _term_pattern(term: str) -> str:
    return _BOUND_L + re.escape(term) + _BOUND_R


@lru_cache(maxsize=1)
def _compiled():
    """Return list of (skill, regex, is_ambiguous)."""
    items = []
    for skill, (_cat, aliases) in SKILLS.items():
        for term in {skill, *aliases}:
            low = term.lower()
            ambiguous = low in AMBIGUOUS_ALIASES or len(low) <= 1
            if len(term) == 1:  # "C", "R" -> must be upper-case single letters
                rx = re.compile(_term_pattern(term.upper()))
            else:
                rx = re.compile(_term_pattern(term), re.IGNORECASE)
            items.append((skill, rx, ambiguous))
    return items


@lru_cache(maxsize=1)
def _needles():
    """Lower-case literal of every term (same order as _compiled) for a fast 'is it even there?' check."""
    out = []
    for skill, (_cat, aliases) in SKILLS.items():
        for term in {skill, *aliases}:
            out.append(None if len(term) == 1 else term.lower())
    return out


def _list_like_text(text: str) -> str:
    """Lines that look like skill lists: contain separators like , | • /"""
    lines = []
    for line in text.splitlines():
        if len(re.findall(r"[,|•·/;]", line)) >= 2 or re.match(r"^\s*(skills?|technologies|tech stack|tools)\b", line, re.I):
            lines.append(line)
    return "\n".join(lines)


def extract_skills(text: str, skills_section: str = "") -> dict:
    """
    Returns {"skills": [..sorted by frequency..],
             "by_category": {cat: [skills]},
             "counts": {skill: n}}
    """
    if not text:
        return {"skills": [], "by_category": {}, "counts": {}}

    safe_zone = (skills_section or "") + "\n" + _list_like_text(text)
    counts = Counter()
    for zone_name, haystack in (("text", text), ("safe", safe_zone)):
        # collect every match with its span, longest first, so that
        # "Tailwind CSS" is not also counted as "CSS", "React Native" not as "React"
        found = []
        hay_low = haystack.lower()
        for (skill, rx, ambiguous), needle in zip(_compiled(), _needles()):
            if zone_name == "text" and ambiguous:
                continue  # short aliases are only trusted inside skill lists
            if needle is not None and needle not in hay_low:
                continue  # fast substring check: skip the regex when the word is not in the text at all
            count_it = (zone_name == "text") or ambiguous
            for m in rx.finditer(haystack):
                found.append((m.end() - m.start(), m.start(), m.end(), skill, count_it))
        found.sort(key=lambda x: (-x[0], x[1]))
        taken = []
        for _ln, st, en, skill, count_it in found:
            if any(st < e and en > s for s, e in taken):
                continue
            taken.append((st, en))
            if count_it:
                counts[skill] += 1

    # "Django REST Framework" implies Django, "Next.js" implies React etc.
    implied = {"Django REST Framework": "Django", "Next.js": "React", "React Native": "React",
               "PostgreSQL": "SQL", "MySQL": "SQL", "Pandas": "Python", "Django": "Python",
               "Flask": "Python", "FastAPI": "Python", "Spring Boot": "Java"}
    for k, v in implied.items():
        if k in counts and v not in counts:
            counts[v] = 1

    ordered = [s for s, _ in counts.most_common()]
    by_cat = {}
    for s in ordered:
        by_cat.setdefault(category_of(s), []).append(s)
    return {"skills": ordered, "by_category": by_cat, "counts": dict(counts)}


def technical_only(skills):
    return [s for s in skills if category_of(s) != SOFT_SKILL_CATEGORY]
