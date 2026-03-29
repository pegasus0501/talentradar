"""
agents/hydradb_agent.py — Agent 1: Internal Candidate Database Search.

What it does:
  1. Embeds the recruiter's requirements using Gemini text-embedding-004.
  2. Runs a semantic vector search against HydraDB's candidates table.
  3. Additionally fetches candidates with matching source='linkedin' stored
     in HydraDB (the synthetic LinkedIn fallback profiles).
  4. Returns up to 20 candidate profiles.

Why vector search?
  Keyword search misses candidates whose profiles use different terminology
  (e.g. "MLOps" vs "Machine Learning Infrastructure"). Semantic embeddings
  capture meaning, not just words.
"""

import asyncio
import time
from gemini_client import GeminiClient
from hydradb_client import HydraDBClient
from models import CandidateProfile, ParsedRequirements


class HydraDBAgent:
    def __init__(self, gemini: GeminiClient, db: HydraDBClient) -> None:
        self._gemini = gemini
        self._db = db

    async def search(
        self,
        requirements: ParsedRequirements,
    ) -> tuple[list[CandidateProfile], float]:
        """
        Run async vector search. Returns (candidates, duration_ms).
        Runs in a thread pool to avoid blocking the event loop during
        the synchronous psycopg2 DB call.
        """
        t0 = time.perf_counter()
        loop = asyncio.get_event_loop()

        candidates = await loop.run_in_executor(None, self._sync_search, requirements)

        duration_ms = (time.perf_counter() - t0) * 1000
        return candidates, duration_ms

    def _sync_search(self, requirements: ParsedRequirements) -> list[CandidateProfile]:
        # Build a rich query string from all requirement fields
        query_text = (
            f"{requirements.role} "
            f"{' '.join(requirements.skills)} "
            f"{' '.join(requirements.focus_areas)} "
            f"{requirements.location or ''}"
        ).strip()

        # Get embedding from Gemini
        embedding = self._gemini.embed_text(query_text)

        # Vector search for internal profiles
        internal = self._db.vector_search(embedding, top_k=15, source_filter="internal")

        # Also pull synthetic LinkedIn profiles stored in HydraDB
        linkedin_in_db = self._db.vector_search(embedding, top_k=10, source_filter="linkedin")

        return internal + linkedin_in_db
