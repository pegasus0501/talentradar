"""
gemini_client.py — Wrapper around the Google Gemini SDK (google-genai).

IMPORTANT: If your API key has quota issues (limit=0 / 429 errors),
set GEMINI_FALLBACK=true in .env — the app will use keyword-based
parsing and scoring without any API calls.

Key methods
-----------
parse_requirements(prompt)            → ParsedRequirements
embed_text(text)                      → List[float]
score_candidates(requirements, candidates) → List[dict]
"""

import json
import os
import re
import random
from typing import Any

from models import CandidateProfile, ParsedRequirements

# ── Config ────────────────────────────────────────────────────────────────────
# PLACEHOLDER: Set GEMINI_API_KEY in your .env file
# Get your key at: https://aistudio.google.com/app/apikey
_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Set GEMINI_FALLBACK=true to skip all API calls (keyword scoring only)
_FALLBACK = os.getenv("GEMINI_FALLBACK", "false").lower() == "true" or not _API_KEY

_CHAT_MODEL  = "models/gemini-2.0-flash-lite"
_EMBED_MODEL = "models/text-embedding-004"

# Initialise Gemini client only if not in fallback mode
_client = None
if not _FALLBACK:
    try:
        from google import genai
        from google.genai import types as _types
        _client = genai.Client(api_key=_API_KEY)
    except Exception as e:
        print(f"⚠️  Gemini init failed ({e}). Falling back to keyword mode.")
        _FALLBACK = True


# ── Retry helper ──────────────────────────────────────────────────────────────
def _call_with_retry(fn, *args, max_retries=2, **kwargs):
    import time
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            is_quota = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if is_quota and attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                print(f"⏳ Gemini 429 — retrying in {wait}s")
                time.sleep(wait)
            else:
                raise


# ── Keyword fallback helpers ───────────────────────────────────────────────────
_SKILL_KW = ["python","go","rust","java","kubernetes","docker","kafka","spark",
              "pytorch","tensorflow","react","typescript","aws","gcp","redis",
              "postgres","grpc","langchain","ray","elasticsearch","ml","ai"]
_FOCUS_KW = ["distributed systems","ai/ml","mlops","llm","data infrastructure",
             "real-time","cloud","platform","nlp","recommendation","search",
             "computer vision","backend","frontend"]
_EXP_RE   = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)", re.IGNORECASE)
_LOC_RE   = re.compile(
    r"\b(san francisco|new york|seattle|austin|remote|los angeles|boston|chicago|denver|nyc|sf)\b",
    re.IGNORECASE,
)


def _keyword_parse(prompt: str) -> ParsedRequirements:
    p = prompt.lower()
    skills     = [k for k in _SKILL_KW if k in p]
    focus      = [f for f in _FOCUS_KW if f in p]
    exp_match  = _EXP_RE.search(prompt)
    years_min  = int(exp_match.group(1)) if exp_match else 0
    loc_match  = _LOC_RE.search(prompt)
    location   = loc_match.group(0).title() if loc_match else None

    # Guess role from common titles
    role = "Software Engineer"
    for t in ["ml engineer","machine learning","staff engineer","principal","backend","frontend",
              "platform","sre","data engineer","ai engineer","distributed"]:
        if t in p:
            role = t.title()
            break

    return ParsedRequirements(
        role=role,
        skills=skills[:6],
        focus_areas=focus[:3],
        years_exp_min=years_min,
        location=location,
    )


def _keyword_score(requirements: ParsedRequirements, candidate: CandidateProfile) -> dict:
    score  = 0
    strengths, gaps = [], []

    # Skills overlap (up to 40 pts)
    req_skills = {s.lower() for s in requirements.skills}
    cand_skills = {s.lower() for s in candidate.skills}
    matched = req_skills & cand_skills
    skill_score = min(len(matched) / max(len(req_skills), 1), 1.0) * 40
    score += skill_score
    if matched:
        strengths.append(f"Matches skills: {', '.join(list(matched)[:3])}")
    missing = req_skills - cand_skills
    if missing:
        gaps.append(f"Missing: {', '.join(list(missing)[:3])}")

    # Focus areas (up to 25 pts)
    req_focus  = {f.lower() for f in requirements.focus_areas}
    cand_focus = {f.lower() for f in candidate.focus_areas}
    matched_f  = req_focus & cand_focus
    score += min(len(matched_f) / max(len(req_focus), 1), 1.0) * 25
    if matched_f:
        strengths.append(f"Focus area match: {list(matched_f)[0]}")

    # Experience (up to 20 pts)
    if candidate.years_experience >= requirements.years_exp_min:
        exp_bonus = min(candidate.years_experience / max(requirements.years_exp_min, 1), 1.5)
        score += min(exp_bonus * 13, 20)
        strengths.append(f"{candidate.years_experience} years experience")
    else:
        deficit = requirements.years_exp_min - candidate.years_experience
        gaps.append(f"{deficit} years short of required experience")

    # Location (15 pts)
    if requirements.location:
        if requirements.location.lower() in candidate.location.lower():
            score += 15
            strengths.append(f"Located in {candidate.location}")
        elif "remote" in candidate.location.lower():
            score += 8

    final = min(round(score), 100)
    explanation = (
        f"{candidate.name} scores {final}/100 — "
        f"{strengths[0] if strengths else 'partial match'}."
    )
    return {
        "id": candidate.id,
        "score": final,
        "explanation": explanation,
        "strengths": strengths[:3],
        "gaps": gaps[:2],
    }


# ── Main client class ─────────────────────────────────────────────────────────
class GeminiClient:

    def parse_requirements(self, prompt: str) -> ParsedRequirements:
        if _FALLBACK:
            print("ℹ️  Using keyword parser (GEMINI_FALLBACK mode)")
            return _keyword_parse(prompt)

        from google.genai import types
        system_prompt = (
            "You are a helpful assistant for an HR platform. "
            "Extract structured requirements from the recruiter's prompt. "
            "Respond ONLY with valid JSON:\n"
            '{"role":"string","skills":["string"],"focus_areas":["string"],'
            '"years_exp_min":0,"location":"string or null","extra_notes":"string or null"}'
        )
        try:
            response = _call_with_retry(
                _client.models.generate_content,
                model=_CHAT_MODEL,
                contents=f"{system_prompt}\n\nRecruiter prompt:\n{prompt}",
                config=types.GenerateContentConfig(
                    temperature=0.1, response_mime_type="application/json"
                ),
            )
            return ParsedRequirements(**json.loads(response.text))
        except Exception as e:
            print(f"⚠️  Gemini parse failed ({e}), using keyword fallback")
            return _keyword_parse(prompt)

    def embed_text(self, text: str) -> list[float]:
        if _FALLBACK or _client is None:
            # Return a random unit vector as stub (vector search won't be used in mock mode)
            v = [random.gauss(0, 1) for _ in range(768)]
            norm = sum(x**2 for x in v) ** 0.5
            return [x / norm for x in v]

        from google.genai import types
        result = _call_with_retry(
            _client.models.embed_content,
            model=_EMBED_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        return result.embeddings[0].values

    def score_candidates(
        self,
        requirements: ParsedRequirements,
        candidates: list[CandidateProfile],
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []

        if _FALLBACK:
            print("ℹ️  Using keyword scorer (GEMINI_FALLBACK mode)")
            scored = [_keyword_score(requirements, c) for c in candidates]
            return sorted(scored, key=lambda x: x["score"], reverse=True)

        from google.genai import types
        req_text = (
            f"Role: {requirements.role}\n"
            f"Skills: {', '.join(requirements.skills)}\n"
            f"Focus: {', '.join(requirements.focus_areas)}\n"
            f"Min Exp: {requirements.years_exp_min} years\n"
            f"Location: {requirements.location or 'Any'}"
        )
        candidates_text = "\n\n".join(
            f"ID: {c.id}\nName: {c.name}\nTitle: {c.title} @ {c.current_company or '?'}\n"
            f"Location: {c.location}\nExp: {c.years_experience}y\n"
            f"Skills: {', '.join(c.skills)}\nFocus: {', '.join(c.focus_areas)}\nBio: {c.bio}"
            for c in candidates
        )
        prompt = (
            "You are an expert technical recruiter AI.\n\n"
            f"REQUIREMENTS:\n{req_text}\n\nCANDIDATES:\n{candidates_text}\n\n"
            "Score each 0-100. Respond ONLY with JSON array sorted highest to lowest:\n"
            '[{"id":"str","score":0,"explanation":"one sentence","strengths":["str"],"gaps":["str"]}]'
        )
        try:
            response = _call_with_retry(
                _client.models.generate_content,
                model=_CHAT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2, response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"⚠️  Gemini score failed ({e}), using keyword fallback")
            scored = [_keyword_score(requirements, c) for c in candidates]
            return sorted(scored, key=lambda x: x["score"], reverse=True)
