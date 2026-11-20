"""
Resume <-> Job matching engine.

final_score = 60% skill overlap + 30% semantic similarity + 10% experience fit

Semantic similarity uses Sentence-Transformers (all-MiniLM-L6-v2) when it is
installed, otherwise TF-IDF + cosine similarity (scikit-learn). Both give the
same API, so the rest of the app does not care which one is active.
"""
import logging
from functools import lru_cache

from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skill_extractor import extract_skills, technical_only

log = logging.getLogger(__name__)

W_SKILL, W_SEMANTIC, W_EXP = 0.6, 0.3, 0.1


@lru_cache(maxsize=1)
def _embedding_model():
    backend = getattr(settings, "MATCHER_BACKEND", "auto")
    if backend == "tfidf":
        return None
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        log.info("Matcher: using sentence-transformers")
        return model
    except Exception as e:  # not installed / no internet to download model
        log.info("Matcher: falling back to TF-IDF (%s)", e)
        return None


def matcher_backend_name():
    return "Sentence-Transformers (BERT embeddings)" if _embedding_model() else "TF-IDF + Cosine Similarity"


def _semantic_scores(resume_text: str, job_texts: list) -> list:
    if not job_texts:
        return []
    model = _embedding_model()
    if model is not None:
        vecs = model.encode([resume_text[:5000]] + [t[:5000] for t in job_texts], normalize_embeddings=True)
        sims = (vecs[1:] @ vecs[0]).tolist()
        # MiniLM similarities for related docs are ~0.2-0.7 -> stretch to 0-1
        return [max(0.0, min(1.0, (s - 0.15) / 0.55)) for s in sims]

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=20000, sublinear_tf=True)
    try:
        m = vec.fit_transform([resume_text] + job_texts)
    except ValueError:  # empty vocabulary
        return [0.0] * len(job_texts)
    sims = cosine_similarity(m[0:1], m[1:]).flatten().tolist()
    return [max(0.0, min(1.0, s * 2.5)) for s in sims]


def match_jobs(resume_text: str, resume_skills: list, resume_exp: float, jobs: list) -> list:
    """
    jobs: list of dicts {"id", "text", "skills" (optional list), "min_experience" (optional)}
    returns list of dicts (same order) with score + matched/missing skills.
    """
    resume_set = {s.lower() for s in resume_skills}
    semantic = _semantic_scores(resume_text, [j["text"] for j in jobs])
    results = []
    for job, sem in zip(jobs, semantic):
        job_skills = list(dict.fromkeys((job.get("skills") or []) + extract_skills(job["text"])["skills"]))
        job_tech = technical_only(job_skills) or job_skills
        matched = [s for s in job_tech if s.lower() in resume_set]
        missing = [s for s in job_tech if s.lower() not in resume_set]

        if job_tech:
            skill_score = len(matched) / len(job_tech)
            w_skill, w_sem = W_SKILL, W_SEMANTIC
        else:  # job text has no recognisable skills -> rely on semantics
            skill_score, w_skill, w_sem = 0.0, 0.0, W_SKILL + W_SEMANTIC

        min_exp = job.get("min_experience") or 0
        exp_score = 1.0 if not min_exp else min(1.0, (resume_exp or 0) / min_exp)

        final = w_skill * skill_score + w_sem * sem + W_EXP * exp_score
        results.append({
            "id": job.get("id"),
            "score": round(final * 100, 1),
            "skill_score": round(skill_score * 100, 1),
            "semantic_score": round(sem * 100, 1),
            "experience_score": round(exp_score * 100, 1),
            "matched_skills": matched,
            "missing_skills": missing[:12],
            "job_skills": job_tech,
        })
    return results


def match_one(resume_text, resume_skills, resume_exp, job_text, job_skills=None, min_experience=0):
    return match_jobs(resume_text, resume_skills, resume_exp,
                      [{"id": None, "text": job_text, "skills": job_skills or [], "min_experience": min_experience}])[0]


def match_label(score: float) -> str:
    if score >= 75:
        return "Excellent Match"
    if score >= 55:
        return "Good Match"
    if score >= 35:
        return "Fair Match"
    return "Low Match"
