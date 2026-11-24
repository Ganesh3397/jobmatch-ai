"""
Live job providers.

Needs a (free) key:
* Adzuna    - https://developer.adzuna.com  (country "in" = India city jobs)
* JSearch   - RapidAPI key: LinkedIn / Indeed / Glassdoor via Google for Jobs

No key needed (enabled by FREE_JOB_APIS=True):
* Remotive  - https://remotive.com/api/remote-jobs     (remote tech jobs, worldwide)
* Jobicy    - https://jobicy.com/api/v2/remote-jobs    (remote jobs)
* Arbeitnow - https://www.arbeitnow.com/api/job-board-api (EU + remote jobs)

Company careers pages (no key, enabled by listing companies in CAREER_BOARDS):
* Greenhouse - boards-api.greenhouse.io (official public job-board API)
* Lever      - api.lever.co/v0/postings  (official public postings API)

Each provider returns a list of normalised dicts that map 1:1 to the Job model.
"""
import html
import logging
import re
from datetime import datetime, timezone

import requests
from django.conf import settings

log = logging.getLogger(__name__)
TIMEOUT = (4, 6)  # (connect, read) seconds - a slow site must not slow the whole page
# Some job sites block the default "python-requests" client -> identify like a normal app
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 JobMatchAI/1.0",
    "Accept": "application/json",
}


def http_get(url, params=None, headers=None):
    h = dict(HEADERS)
    h.update(headers or {})
    r = requests.get(url, params=params, headers=h, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def _strip_html(s):
    s = re.sub(r"<\s*(br|/p|/li|/h\d)[^>]*>", "\n", s or "", flags=re.I)
    s = re.sub(r"<li[^>]*>", "\n- ", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n\n", s).strip()


GENERIC = {"developer", "engineer", "jobs", "job", "senior", "junior", "and", "the", "for", "with", "/", "-"}


def keyword_for(query):
    """'Python Developer' -> 'python', 'Full Stack Developer' -> 'full stack' (for keyword-only APIs)."""
    words = [w for w in re.findall(r"[A-Za-z+#.]+", query.lower()) if w not in GENERIC]
    return " ".join(words[:2]) or query.lower()


def _job_type(value):
    v = " ".join(value) if isinstance(value, list) else str(value or "")
    v = v.lower()
    if "intern" in v:
        return "internship"
    if "part" in v:
        return "part_time"
    if "contract" in v or "freelance" in v:
        return "contract"
    return "full_time"


def _to_int(v):
    try:
        return int(float(v)) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _parse_dt(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class AdzunaProvider:
    name = "adzuna"
    BASE = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

    @staticmethod
    def enabled():
        return bool(settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY)

    def search(self, query, location="", page=1, per_page=30):
        params = {
            "app_id": settings.ADZUNA_APP_ID,
            "app_key": settings.ADZUNA_APP_KEY,
            "what": query,
            "results_per_page": per_page,
            "content-type": "application/json",
            "sort_by": "date",
        }
        if location:
            params["where"] = location
        url = self.BASE.format(country=settings.ADZUNA_COUNTRY, page=page)
        r = http_get(url, params=params)
        out = []
        for j in r.json().get("results", []):
            contract = (j.get("contract_time") or "").lower()
            out.append({
                "source": self.name,
                "external_id": str(j.get("id")),
                "title": _strip_html(j.get("title")),
                "company": (j.get("company") or {}).get("display_name", ""),
                "location": (j.get("location") or {}).get("display_name", ""),
                "description": _strip_html(j.get("description")),
                "apply_url": j.get("redirect_url", ""),
                "salary_min": int(j["salary_min"]) if j.get("salary_min") else None,
                "salary_max": int(j["salary_max"]) if j.get("salary_max") else None,
                "job_type": "part_time" if contract == "part_time" else "full_time",
                "work_mode": "remote" if "remote" in (j.get("title", "") + j.get("description", "")).lower() else "onsite",
                "posted_at": _parse_dt(j.get("created")),
            })
        return out


class JSearchProvider:
    name = "jsearch"
    URL = "https://jsearch.p.rapidapi.com/search"

    @staticmethod
    def enabled():
        return bool(settings.JSEARCH_API_KEY)

    def search(self, query, location="", page=1, per_page=30):
        q = f"{query} in {location or 'India'}"
        headers = {"X-RapidAPI-Key": settings.JSEARCH_API_KEY, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}
        r = http_get(self.URL, params={"query": q, "page": page, "num_pages": 1}, headers=headers)
        out = []
        for j in r.json().get("data", []):
            etype = (j.get("job_employment_type") or "").upper()
            loc = ", ".join(x for x in [j.get("job_city"), j.get("job_state"), j.get("job_country")] if x)
            exp_months = ((j.get("job_required_experience") or {}).get("required_experience_in_months")) or 0
            out.append({
                "source": self.name,
                "external_id": str(j.get("job_id")),
                "title": j.get("job_title", ""),
                "company": j.get("employer_name", ""),
                "location": loc,
                "description": (j.get("job_description") or "")[:6000],
                "apply_url": j.get("job_apply_link", ""),
                "publisher": (j.get("job_publisher") or "")[:80],
                "salary_min": int(j["job_min_salary"]) if j.get("job_min_salary") else None,
                "salary_max": int(j["job_max_salary"]) if j.get("job_max_salary") else None,
                "job_type": {"INTERN": "internship", "PARTTIME": "part_time",
                             "CONTRACTOR": "contract"}.get(etype, "full_time"),
                "work_mode": "remote" if j.get("job_is_remote") else "onsite",
                "min_experience": round(exp_months / 12, 1),
                "posted_at": _parse_dt(j.get("job_posted_at_datetime_utc")),
            })
        return out


class RemotiveProvider:
    name = "remotive"
    URL = "https://remotive.com/api/remote-jobs"

    @staticmethod
    def enabled():
        return getattr(settings, "FREE_JOB_APIS", True)

    def search(self, query, location="", page=1, per_page=30):
        r = http_get(self.URL, params={"search": keyword_for(query), "limit": per_page})
        out = []
        for j in r.json().get("jobs", []):
            out.append({
                "source": self.name,
                "external_id": str(j.get("id")),
                "title": html.unescape(j.get("title") or ""),
                "company": j.get("company_name", ""),
                "location": f"Remote ({j.get('candidate_required_location') or 'Worldwide'})",
                "description": _strip_html(j.get("description"))[:8000],
                "apply_url": j.get("url", ""),
                "job_type": _job_type(j.get("job_type")),
                "work_mode": "remote",
                "posted_at": _parse_dt(j.get("publication_date")),
            })
        return out


class JobicyProvider:
    name = "jobicy"
    URL = "https://jobicy.com/api/v2/remote-jobs"

    @staticmethod
    def enabled():
        return getattr(settings, "FREE_JOB_APIS", True)

    def search(self, query, location="", page=1, per_page=30):
        params = {"count": per_page}
        kw = keyword_for(query)
        if 3 <= len(kw) <= 50:
            params["tag"] = kw
        r = http_get(self.URL, params=params)
        out = []
        for j in r.json().get("jobs", []):
            out.append({
                "source": self.name,
                "external_id": str(j.get("id")),
                "title": html.unescape(j.get("jobTitle") or ""),
                "company": html.unescape(j.get("companyName") or ""),
                "location": f"Remote ({j.get('jobGeo') or 'Anywhere'})",
                "description": _strip_html(j.get("jobDescription") or j.get("jobExcerpt"))[:8000],
                "apply_url": j.get("url", ""),
                "job_type": _job_type(j.get("jobType")),
                "work_mode": "remote",
                "salary_min": _to_int(j.get("annualSalaryMin")) if j.get("salaryCurrency") == "INR" else None,
                "salary_max": _to_int(j.get("annualSalaryMax")) if j.get("salaryCurrency") == "INR" else None,
                "posted_at": _parse_dt(j.get("pubDate")),
            })
        return out


class ArbeitnowProvider:
    """No search parameter -> fetch latest page and keep jobs matching the keyword."""
    name = "arbeitnow"
    URL = "https://www.arbeitnow.com/api/job-board-api"

    @staticmethod
    def enabled():
        return getattr(settings, "FREE_JOB_APIS", True)

    def search(self, query, location="", page=1, per_page=30):
        r = http_get(self.URL, params={"page": page})
        words = keyword_for(query).split()
        out = []
        for j in r.json().get("data", []):
            hay = f"{j.get('title', '')} {' '.join(j.get('tags') or [])}".lower()
            if words and not all(w in hay for w in words):
                continue
            ts = j.get("created_at")
            out.append({
                "source": self.name,
                "external_id": str(j.get("slug")),
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "location": ("Remote / " if j.get("remote") else "") + (j.get("location") or "Europe"),
                "description": _strip_html(j.get("description"))[:8000],
                "apply_url": j.get("url", ""),
                "job_type": _job_type(j.get("job_types")),
                "work_mode": "remote" if j.get("remote") else "onsite",
                "posted_at": datetime.fromtimestamp(ts, tz=timezone.utc) if isinstance(ts, (int, float)) else None,
            })
        return out[:per_page]


def _career_boards(kind):
    """
    CAREER_BOARDS=greenhouse:razorpay,lever:cred=CRED   ->  [("razorpay", "Razorpay")] for kind="greenhouse"
    The slug is the last part of the company's careers URL:
      boards.greenhouse.io/<slug>  or  job-boards.greenhouse.io/<slug>  or  jobs.lever.co/<slug>
    """
    out = []
    for item in getattr(settings, "CAREER_BOARDS", []):
        k, _, rest = item.partition(":")
        if k.strip().lower() != kind or not rest.strip():
            continue
        slug, _, name = rest.partition("=")
        slug = slug.strip()
        out.append((slug, name.strip() or slug.replace("-", " ").title()))
    return out[:15]


def _wanted(query, location, title, text, job_location):
    """Keep a career-page job only if it fits the search (career pages list every opening of the company)."""
    words = keyword_for(query).split()
    hay = f"{title} {text[:2500]}".lower()
    if words and not all(w in hay for w in words):
        return False
    if location:
        loc = (job_location or "").lower()
        if location.lower() not in loc and "remote" not in loc:
            return False
    return True


def _many(boards, fetch):
    from concurrent.futures import ThreadPoolExecutor
    if not boards:
        return []
    out, errors = [], []

    def one(board):
        try:
            return fetch(*board)
        except Exception as e:  # one company's page failing must not hide the others
            errors.append(f"{board[0]}: {e.__class__.__name__}")
            return []
    with ThreadPoolExecutor(max_workers=min(6, len(boards))) as pool:
        for jobs in pool.map(one, boards):
            out.extend(jobs)
    if errors and not out:
        raise RuntimeError("career pages failed - " + ", ".join(errors[:3]))
    return out


class GreenhouseProvider:
    """Official public job-board API used by many companies for their careers page (no key needed)."""
    name = "greenhouse"
    URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    @staticmethod
    def enabled():
        return bool(_career_boards("greenhouse"))

    def search(self, query, location="", page=1, per_page=30):
        def fetch(slug, company):
            r = http_get(self.URL.format(slug=slug), params={"content": "true"})
            jobs = []
            for j in r.json().get("jobs", []):
                desc = _strip_html(html.unescape(j.get("content") or ""))[:8000]
                loc = (j.get("location") or {}).get("name", "")
                if not _wanted(query, location, j.get("title", ""), desc, loc):
                    continue
                jobs.append({
                    "source": self.name, "external_id": f"{slug}-{j.get('id')}", "title": j.get("title", ""),
                    "company": company, "location": loc, "description": desc or j.get("title", ""),
                    "apply_url": j.get("absolute_url", ""), "publisher": f"{company} careers",
                    "job_type": _job_type(j.get("title")),
                    "work_mode": "remote" if "remote" in loc.lower() else "onsite",
                    "posted_at": _parse_dt(j.get("updated_at")),
                })
            return jobs
        return _many(_career_boards("greenhouse"), fetch)[:per_page]


class LeverProvider:
    """Official public postings API of Lever careers pages (no key needed)."""
    name = "lever"
    URL = "https://api.lever.co/v0/postings/{slug}"

    @staticmethod
    def enabled():
        return bool(_career_boards("lever"))

    def search(self, query, location="", page=1, per_page=30):
        def fetch(slug, company):
            r = http_get(self.URL.format(slug=slug), params={"mode": "json"})
            jobs = []
            for j in r.json():
                cat = j.get("categories") or {}
                loc = cat.get("location") or ""
                parts = [j.get("descriptionPlain") or ""] + \
                        [f"{x.get('text', '')}\n{_strip_html(x.get('content'))}" for x in (j.get("lists") or [])]
                desc = "\n\n".join(p for p in parts if p).strip()[:8000]
                if not _wanted(query, location, j.get("text", ""), desc, loc):
                    continue
                ts = j.get("createdAt")
                jobs.append({
                    "source": self.name, "external_id": f"{slug}-{j.get('id')}", "title": j.get("text", ""),
                    "company": company, "location": loc, "description": desc or j.get("text", ""),
                    "apply_url": j.get("hostedUrl") or j.get("applyUrl", ""), "publisher": f"{company} careers",
                    "job_type": _job_type(cat.get("commitment")),
                    "work_mode": "remote" if "remote" in (loc + " " + (j.get("workplaceType") or "")).lower() else "onsite",
                    "posted_at": datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if isinstance(ts, (int, float)) else None,
                })
            return jobs
        return _many(_career_boards("lever"), fetch)[:per_page]


PROVIDERS = (AdzunaProvider, JSearchProvider, RemotiveProvider, JobicyProvider, ArbeitnowProvider,
             GreenhouseProvider, LeverProvider)
LIVE_SOURCES = [p.name for p in PROVIDERS]


def active_providers():
    return [p() for p in PROVIDERS if p.enabled()]
