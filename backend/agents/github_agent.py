"""
agents/github_agent.py — Agent 2: GitHub Public Profile Search.

What it does:
  1. Calls GitHub's free REST Search API (/search/users) with a query
     built from the requirements (language, location, keywords).
  2. Fetches detailed profiles for up to 10 matching users.
  3. Returns normalised CandidateProfile objects with source="github".

Rate limits:
  - Unauthenticated: 10 req/min search, 60 req/min user lookups
  - Authenticated (GITHUB_TOKEN):  30 req/min search, 5 000 req/hr
  We recommend setting GITHUB_TOKEN in .env to avoid limit issues.

Fallback:
  If GitHub API is unreachable or rate-limited, returns empty list
  (the orchestrator marks this agent as "error" but continues).
"""

import asyncio
import os
import time
from typing import Optional
import httpx

from models import CandidateProfile, ParsedRequirements

# PLACEHOLDER: Set GITHUB_TOKEN in your .env file (optional but recommended)
_GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
_BASE_URL = "https://api.github.com"
_HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {_GITHUB_TOKEN}"} if _GITHUB_TOKEN else {}),
}


class GitHubAgent:
    async def search(
        self,
        requirements: ParsedRequirements,
    ) -> tuple[list[CandidateProfile], float]:
        t0 = time.perf_counter()
        candidates = await self._fetch_candidates(requirements)
        return candidates, (time.perf_counter() - t0) * 1000

    async def _fetch_candidates(
        self,
        requirements: ParsedRequirements,
    ) -> list[CandidateProfile]:
        # Build a GitHub user search query
        # e.g. "distributed systems AI ML location:San Francisco language:Python"
        keywords = " ".join(requirements.focus_areas + requirements.skills[:3])
        location_q = f"location:{requirements.location}" if requirements.location else ""
        q = f"{keywords} {location_q}".strip()

        try:
            async with httpx.AsyncClient(headers=_HEADERS, timeout=10) as client:
                search_resp = await client.get(
                    f"{_BASE_URL}/search/users",
                    params={"q": q, "per_page": 10, "sort": "followers"},
                )
                search_resp.raise_for_status()
                items = search_resp.json().get("items", [])

                # Fetch user details in parallel (up to 10)
                tasks = [
                    self._fetch_user(client, item["login"])
                    for item in items[:10]
                ]
                profiles = await asyncio.gather(*tasks, return_exceptions=True)

            return [p for p in profiles if isinstance(p, CandidateProfile)]

        except Exception:
            # Graceful degradation — return empty, orchestrator handles it
            return []

    async def _fetch_user(
        self,
        client: httpx.AsyncClient,
        username: str,
    ) -> Optional[CandidateProfile]:
        try:
            resp = await client.get(f"{_BASE_URL}/users/{username}")
            resp.raise_for_status()
            u = resp.json()

            # Estimate years of experience from public_repos as a rough proxy
            repos = u.get("public_repos", 0)
            est_years = min(max(repos // 10, 1), 15)

            name = u.get("name") or username
            bio  = u.get("bio") or ""
            company = (u.get("company") or "").strip().lstrip("@")
            location = u.get("location") or "Remote"
            avatar = u.get("avatar_url", "")
            blog   = u.get("blog", "")
            html_url = u.get("html_url", f"https://github.com/{username}")

            # Infer some skills/focus areas from the bio text
            skills = _infer_skills_from_bio(bio)

            return CandidateProfile(
                id=f"gh_{username}",
                name=name,
                title="Software Engineer",
                location=location,
                years_experience=est_years,
                skills=skills,
                focus_areas=_infer_focus(bio),
                bio=bio or f"GitHub user with {repos} public repositories.",
                github_url=html_url,
                github_username=username,
                linkedin_url=blog if "linkedin" in blog else None,
                current_company=company or None,
                avatar_url=avatar,
                source="github",
            )
        except Exception:
            return None


# ── Bio analysis helpers ───────────────────────────────────────────────────────

_SKILL_KEYWORDS = {
    "Python": ["python", "django", "flask", "fastapi"],
    "Go": ["golang", " go ", "gin"],
    "Rust": ["rust"],
    "TypeScript": ["typescript", "ts"],
    "JavaScript": ["javascript", "js", "node"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Docker": ["docker"],
    "ML": ["ml ", "machine learning", "llm", "deep learning"],
    "AI": ["ai ", "artificial intelligence", "gpt", "llm"],
    "Distributed Systems": ["distributed", "kafka", "spark", "flink"],
    "Cloud": ["aws", "gcp", "azure", "cloud"],
    "React": ["react"],
    "Postgres": ["postgres", "postgresql"],
}

_FOCUS_KEYWORDS = {
    "AI/ML": ["ai", "ml", "machine learning", "deep learning", "llm", "gpt"],
    "Distributed Systems": ["distributed", "kafka", "spark", "microservices"],
    "Cloud Infrastructure": ["kubernetes", "docker", "cloud", "devops", "k8s"],
    "Backend": ["backend", "api", "server", "database"],
    "Frontend": ["frontend", "react", "vue", "ui"],
    "Open Source": ["open source", "oss"],
}


def _infer_skills_from_bio(bio: str) -> list[str]:
    b = bio.lower()
    return [skill for skill, kws in _SKILL_KEYWORDS.items() if any(kw in b for kw in kws)][:6] or ["GitHub Developer"]


def _infer_focus(bio: str) -> list[str]:
    b = bio.lower()
    return [area for area, kws in _FOCUS_KEYWORDS.items() if any(kw in b for kw in kws)][:3] or ["Software Engineering"]
