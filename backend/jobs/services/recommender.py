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
    """Save fetched jobs with a few bulk queries (one query per job was slow on a remote database)."""
    rows = {}
    for d in job_dicts:
        if d.get("external_id") and d.get("title"):
            rows[(d["source"], str(d["external_id"])[:200])] = d
    if not rows:
        return []
    existing = {(j.source, j.external_id): j for j in Job.objects.filter(
        source__in={k[0] for k in rows}, external_id__in=[k[1] for k in rows])}
    now = timezone.now()
    new, changed = [], []
    for (src, ext), d in rows.items():
        job = existing.get((src, ext))
        if job is None:
            fields = {k: v for k, v in d.items() if k not in ("source", "external_id")}
            fields["skills"] = extract_skills(f"{d['title']}\n{d.get('description', '')}")["skills"][:20]
            new.append(Job(source=src, external_id=ext, search_query=query[:200], is_active=True, **fields))
        else:  # already known: just mark it fresh (skills were extracted the first time)
            job.is_active, job.search_query, job.updated_at = True, query[:200], now
            changed.append(job)
    if new:
        Job.objects.bulk_create(new, ignore_conflicts=True)
    if changed:
        Job.objects.bulk_update(changed, ["is_active", "search_query", "updated_at"])
    ids = dict(Job.objects.filter(source__in={k[0] for k in rows}, external_id__in=[k[1] for k in rows])
               .values_list("external_id", "id"))
    return [ids[k[1]] for k in rows if k[1] in ids]


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


RESULT_TTL = 60 * 15  # ranked results per resume + search are reused for 15 minutes


def _rank(resume, query, location, explicit, force_refresh):
    live_ids, meta = fetch_live_jobs(query, location, force=force_refresh)
    ids = list(dict.fromkeys(live_ids + _local_candidates(query, resume.skills, location, explicit)))
    qs = Job.objects.filter(id__in=ids, is_active=True)
    # real live jobs found -> hide the sample/demo jobs completely
    if live_ids:
        qs = qs.exclude(source=Job.Source.DEMO)
    jobs = list(qs.only("id", "title", "description", "skills", "min_experience", "source"))
    scored = match_jobs(
        resume.raw_text, resume.skills, resume.experience_years,
        [{"id": j.id, "text": j.text_for_matching, "skills": j.skills, "min_experience": j.min_experience,
          "skills_ready": j.source in LIVE_SOURCES}
         for j in jobs],
    )
    by_id = {j.id: j for j in jobs}
    words = _query_words(query)
    for s in scored:
        s["label"] = match_label(s["score"])
        title = by_id[s["id"]].title.lower()
        # relevance of the job title to what the user searched (0..1)
        s["query_relevance"] = round(sum(w in title for w in words) / len(words), 2) if words else 0
    return scored, meta


def recommend_jobs(resume, query="", location="", job_type="", work_mode="", min_score=0,
                   limit=30, force_refresh=False):
    explicit = bool(query and query.strip())
    query = (query or default_query_for(resume)).strip()
    stamp = resume.processed_at.timestamp() if resume.processed_at else 0
    key = "rec:" + hashlib.md5(f"{resume.id}|{stamp}|{explicit}|{query.lower()}|{location.lower().strip()}"
                               .encode()).hexdigest()
    cached = None if force_refresh else cache.get(key)
    if cached:
        scored, meta = cached
        meta = dict(meta, cached=True)
    else:
        scored, meta = _rank(resume, query, location, explicit, force_refresh)
        cache.set(key, (scored, meta), RESULT_TTL)

    # filters only pick from the already ranked list, so changing a filter is instant
    jobs = Job.objects.filter(id__in=[s["id"] for s in scored], is_active=True)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if work_mode:
        jobs = jobs.filter(work_mode=work_mode)
    by_id = {j.id: j for j in jobs}
    results = [{"job": by_id[s["id"]], "match": s} for s in scored
               if s["id"] in by_id and s["score"] >= min_score]
    boost = 40 if explicit else 10
    results.sort(key=lambda r: (r["match"]["score"] + boost * r["match"]["query_relevance"],
                                r["job"].posted_at or r["job"].created_at), reverse=True)

    meta = dict(meta)
    meta.update({
        "query": query,
        "location": location,
        "total_found": len(results),
        "live_enabled": bool(meta["providers"]),
        "generated_at": timezone.now().isoformat(),
    })
    return results[:limit], meta
