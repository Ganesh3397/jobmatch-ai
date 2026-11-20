"""
Real-time job recommendation engine.

1. Decide a search query from the resume (top predicted role) or user input.
2. Fetch live jobs from providers (Adzuna / JSearch) -> cached in Redis for 6h
   and stored in PostgreSQL (so analytics + saved jobs work).
3. Add jobs posted by recruiters on this platform.
4. Score every job against the resume with the AI matcher and sort.
"""
import hashlib
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from resumes.ml.matcher import match_jobs, match_label
from resumes.ml.skill_extractor import extract_skills

from ..models import Job
from .providers import LIVE_SOURCES, active_providers

log = logging.getLogger(__name__)
CACHE_TTL = 60 * 60 * 6  # 6 hours
FAIL_TTL = 60 * 10       # a site that failed is skipped for 10 minutes (keeps the page fast)


def _cache_key(provider, query, location):
    raw = f"{provider}|{query.lower().strip()}|{location.lower().strip()}"
    return "livejobs:" + hashlib.md5(raw.encode()).hexdigest()


def _upsert(job_dicts, query):
    ids = []
    for d in job_dicts:
        if not d.get("external_id") or not d.get("title"):
            continue
        d = dict(d)
        d["skills"] = extract_skills(f"{d['title']}\n{d.get('description', '')}")["skills"][:20]
        d["search_query"] = query[:200]
        d["is_active"] = True
        job, _ = Job.objects.update_or_create(source=d.pop("source"), external_id=d.pop("external_id"), defaults=d)
        ids.append(job.id)
    return ids


def _fetch_one(provider, query, location):
    try:
        return provider.name, provider.search(query, location), None
    except Exception as e:  # network error, bad key, rate limit...
        log.warning("Provider %s failed: %s", provider.name, e)
        detail = str(e).split("\n")[0][:90]
        return provider.name, [], f"{provider.name}: {e.__class__.__name__} ({detail})"


def fetch_live_jobs(query, location="", force=False):
    """
    Returns (job_ids, meta).
    All providers are called IN PARALLEL; results are cached (Redis / memory) for 6h
    so free API rate-limits are respected, and saved in PostgreSQL.
    """
    meta = {"providers": [], "cached": False, "errors": [], "per_source": {}}
    all_ids, to_fetch = [], []
    for provider in active_providers():
        meta["providers"].append(provider.name)
        if not force and cache.get(f"livejobs:down:{provider.name}"):
            meta["errors"].append(f"{provider.name}: skipped (failed recently, retry in a few minutes)")
            meta["per_source"][provider.name] = 0
            continue
        ids = None if force else cache.get(_cache_key(provider.name, query, location))
        if ids is not None:
            meta["cached"] = True
            meta["per_source"][provider.name] = len(ids)
            all_ids.extend(ids)
        else:
            to_fetch.append(provider)

    if to_fetch:
        with ThreadPoolExecutor(max_workers=len(to_fetch)) as pool:
            results = list(pool.map(lambda p: _fetch_one(p, query, location), to_fetch))
        for name, jobs, err in results:  # DB writes stay in the main thread
            ids = _upsert(jobs, query) if jobs else []
            if err:
                meta["errors"].append(err)
                cache.set(f"livejobs:down:{name}", True, FAIL_TTL)
            else:
                cache.set(_cache_key(name, query, location), ids, CACHE_TTL)
            meta["per_source"][name] = len(ids)
            all_ids.extend(ids)
    return all_ids, meta


def _query_words(query):
    return [w.lower() for w in re.findall(r"[A-Za-z+#.]+", query) if len(w) > 1
            and w.lower() not in {"and", "the", "for", "with", "developer", "engineer", "jobs", "job"}]


def _local_candidates(query, skills, location, explicit_query=False, limit=150):
    """Jobs already in DB (recruiter posts, demo data, earlier live fetches)."""
    q = Q()
    words = _query_words(query) or [w.lower() for w in query.split()]
    for word in words[:5]:
        q |= Q(title__icontains=word)
        if explicit_query:
            q |= Q(description__icontains=word)
    if not explicit_query:  # recommendations: also use resume skills
        for s in skills[:8]:
            q |= Q(description__icontains=s) | Q(title__icontains=s)
    # external jobs older than 7 days are probably closed -> skip them
    fresh = timezone.now() - timedelta(days=7)
    qs = Job.objects.filter(is_active=True).filter(
        ~Q(source__in=LIVE_SOURCES) | Q(updated_at__gte=fresh))
    if q:
        qs = qs.filter(q)
    if location:
        qs = qs.filter(Q(location__icontains=location) | Q(work_mode=Job.WorkMode.REMOTE))
    return list(qs.order_by("-created_at").values_list("id", flat=True)[:limit])


def default_query_for(resume):
    if resume.predicted_roles:
        return resume.predicted_roles[0]["role"].split("/")[0].strip()
    return " ".join(resume.skills[:2]) or "software developer"


def recommend_jobs(resume, query="", location="", job_type="", work_mode="", min_score=0,
                   limit=30, force_refresh=False):
    explicit = bool(query and query.strip())
    query = (query or default_query_for(resume)).strip()
    live_ids, meta = fetch_live_jobs(query, location, force=force_refresh)
    ids = list(dict.fromkeys(live_ids + _local_candidates(query, resume.skills, location, explicit)))

    qs = Job.objects.filter(id__in=ids, is_active=True)
    # real live jobs found -> hide the sample/demo jobs completely
    if live_ids:
        qs = qs.exclude(source=Job.Source.DEMO)
    if job_type:
        qs = qs.filter(job_type=job_type)
    if work_mode:
        qs = qs.filter(work_mode=work_mode)
    jobs = list(qs)

    scored = match_jobs(
        resume.raw_text, resume.skills, resume.experience_years,
        [{"id": j.id, "text": j.text_for_matching, "skills": j.skills, "min_experience": j.min_experience}
         for j in jobs],
    )
    by_id = {j.id: j for j in jobs}
    words = _query_words(query)
    results = []
    for s in scored:
        if s["score"] < min_score:
            continue
        s["label"] = match_label(s["score"])
        title = by_id[s["id"]].title.lower()
        # relevance of the job title to what the user searched (0..1)
        s["query_relevance"] = round(sum(w in title for w in words) / len(words), 2) if words else 0
        results.append({"job": by_id[s["id"]], "match": s})
    boost = 40 if explicit else 10
    results.sort(key=lambda r: (r["match"]["score"] + boost * r["match"]["query_relevance"],
                                r["job"].posted_at or r["job"].created_at), reverse=True)

    meta.update({
        "query": query,
        "location": location,
        "total_found": len(results),
        "live_enabled": bool(meta["providers"]),
        "generated_at": timezone.now().isoformat(),
    })
    return results[:limit], meta
