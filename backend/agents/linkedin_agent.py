"""
agents/linkedin_agent.py — Agent 3: LinkedIn Profile Source.

Since LinkedIn's private API requires authentication and web scraping
violates their ToS in production, this agent does the following:

  1. PRIMARY: Returns pre-seeded synthetic LinkedIn-style profiles
     that live in HydraDB with source='linkedin'.  These are already
     stored by the data/generate_candidates.py seed script.
     Vector-filtered by the query requirements.

  2. OPTIONAL REAL SCRAPING (disabled by default):
     If LINKEDIN_SCRAPE=true is set in .env AND you run your own
     scraping proxy, it calls that endpoint.  Swap the stub in
     _real_scrape() with your Apify actor call or SERP API call.

This ensures the demo ALWAYS has LinkedIn profiles to show even
without live scraping infrastructure — critical for a hackathon.
"""

import asyncio
import os
import time
from models import CandidateProfile, ParsedRequirements
from hydradb_client import HydraDBClient

LINKEDIN_SCRAPE = os.getenv("LINKEDIN_SCRAPE", "false").lower() == "true"


class LinkedInAgent:
    def __init__(self, db: HydraDBClient) -> None:
        self._db = db

    async def search(
        self,
        requirements: ParsedRequirements,
    ) -> tuple[list[CandidateProfile], float]:
        t0 = time.perf_counter()
        loop = asyncio.get_event_loop()

        if LINKEDIN_SCRAPE:
            # Optional: hook in a real scraper here
            candidates = await loop.run_in_executor(
                None, self._real_scrape, requirements
            )
        else:
            # Use synthetic LinkedIn profiles already in HydraDB
            candidates = await loop.run_in_executor(
                None, self._fetch_from_db, requirements
            )

        return candidates, (time.perf_counter() - t0) * 1000

    def _fetch_from_db(self, requirements: ParsedRequirements) -> list[CandidateProfile]:
        """
        Pull the best synthetic LinkedIn profiles from HydraDB.
        They were seeded by data/generate_candidates.py with source='linkedin'.
        We do a simple keyword pre-filter then return up to 15.
        """
        all_li = self._db.get_all_candidates(limit=100, source="linkedin")

        # Lightweight client-side filter: prefer location and skill matches
        req_keywords = set(
            (requirements.skills + requirements.focus_areas)
            + ([requirements.location] if requirements.location else [])
        )
        req_keywords = {k.lower() for k in req_keywords}

        def _score(c: CandidateProfile) -> int:
            text = f"{c.location} {' '.join(c.skills)} {' '.join(c.focus_areas)} {c.bio}".lower()
            return sum(1 for kw in req_keywords if kw in text)

        ranked = sorted(all_li, key=_score, reverse=True)
        return ranked[:15]

    def _real_scrape(self, requirements: ParsedRequirements) -> list[CandidateProfile]:
        """
        OPTIONAL: Replace with real scraping logic.
        e.g. call Apify LinkedIn scraper actor, or a SERP API.

        import httpx
        resp = httpx.post(
            "https://api.apify.com/v2/acts/YOUR_ACTOR/run-sync-get-dataset-items",
            params={"token": os.getenv("APIFY_TOKEN")},
            json={"searchQuery": f"{requirements.role} {' '.join(requirements.skills)}"},
        )
        raw = resp.json()
        return [_map_apify_result(r) for r in raw]
        """
        return []  # Stub — implement if you have scraping infrastructure
