"""
Optional Large Language Model (Google Gemini) helper.

* GEMINI_API_KEY set  -> real AI answers from Gemini
* no key / any error  -> returns None and the caller uses the built-in rule engine

So every AI feature keeps working even without a key or internet.
"""
import json
import logging
import re

import requests
from django.conf import settings

log = logging.getLogger(__name__)
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def llm_enabled():
    return bool(getattr(settings, "GEMINI_API_KEY", ""))


def engine_name():
    return f"Google Gemini ({settings.GEMINI_MODEL})" if llm_enabled() else "JobMatch rule-based AI engine"


def ask_json(prompt: str, max_tokens: int = 1500):
    """Ask Gemini for a JSON answer. Returns a dict/list, or None on any problem."""
    if not llm_enabled():
        return None
    try:
        r = requests.post(
            URL.format(model=settings.GEMINI_MODEL),
            headers={"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"},
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.6, "maxOutputTokens": max_tokens,
                                     "responseMimeType": "application/json"},
            },
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"^```(?:json)?|```$", "", text.strip()).strip()
        return json.loads(text)
    except Exception as e:  # bad key, quota, network, invalid JSON...
        log.warning("Gemini call failed, using rule engine: %s", e)
        return None
