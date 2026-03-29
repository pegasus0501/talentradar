"""
agents/orchestrator.py — Master coordinator agent.

Responsibilities:
  1. Call Gemini to parse the recruiter's free-text prompt into structured
     requirements (role, skills, location, years_exp …).
  2. Launch the three search agents IN PARALLEL using asyncio.gather().
  3. Merge and deduplicate all candidate results.
  4. Hand the merged pool to the ScorerAgent.
  5. Return the top-5 ScoredCandidates along with per-agent status metadata.

Why parallel?
  Each agent hits a different network resource (HydraDB, GitHub API, local
  synthetic data). Running them concurrently cuts total latency roughly 3×.
"""

import asyncio
import time
import uuid
from typing import Optional

from gemini_client import GeminiClient
from hydradb_client import HydraDBClient
from models import AgentStatus, CandidateProfile, ParsedRequirements, ScoredCandidate

from .hydradb_agent import HydraDBAgent
from .github_agent import GitHubAgent
from .linkedin_agent import LinkedInAgent
from .scorer import ScorerAgent


class OrchestratorAgent:
    def __init__(self) -> None:
        self._gemini = GeminiClient()
        self._db = HydraDBClient()

    async def run(
        self,
        prompt: str,
    ) -> tuple[
        str,                      # query_id
        ParsedRequirements,       # parsed reqs
        list[ScoredCandidate],    # top-5
        list[AgentStatus],        # per-agent status
        int,                      # total evaluated
        float,                    # total duration ms
    ]:
        t0 = time.perf_counter()
        query_id = str(uuid.uuid4())[:8]

        # ── Step 1: Parse prompt ──────────────────────────────────────────
        requirements = self._gemini.parse_requirements(prompt)

        # ── Step 2: Parallel agent search ────────────────────────────────
        db_agent  = HydraDBAgent(self._gemini, self._db)
        gh_agent  = GitHubAgent()
        li_agent  = LinkedInAgent(self._db)

        results = await asyncio.gather(
            db_agent.search(requirements),
            gh_agent.search(requirements),
            li_agent.search(requirements),
            return_exceptions=True,
        )

        db_result, gh_result, li_result = results

        db_candidates, db_status = self._unpack(db_result, "HydraDB Internal")
        gh_candidates, gh_status = self._unpack(gh_result, "GitHub")
        li_candidates, li_status = self._unpack(li_result, "LinkedIn")

        # ── Step 3: Merge + deduplicate ───────────────────────────────────
        all_candidates = self._deduplicate(db_candidates + gh_candidates + li_candidates)

        # ── Step 4: Score and rank ────────────────────────────────────────
        scorer = ScorerAgent(self._gemini)
        top5   = await scorer.rank(requirements, all_candidates, top_k=5)

        # ── Step 5: Save session to HydraDB ──────────────────────────────
        self._db.save_session(
            query_id,
            prompt,
            {"top_ids": [sc.profile.id for sc in top5]},
        )

        total_ms = (time.perf_counter() - t0) * 1000
        statuses = [db_status, gh_status, li_status]

        return query_id, requirements, top5, statuses, len(all_candidates), total_ms

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _unpack(
        result,
        agent_name: str,
    ) -> tuple[list[CandidateProfile], AgentStatus]:
        """Handle both successful results and exceptions from asyncio.gather."""
        if isinstance(result, Exception):
            return [], AgentStatus(
                name=agent_name,
                status="error",
                results_count=0,
                error=str(result),
            )
        candidates, duration_ms = result
        return candidates, AgentStatus(
            name=agent_name,
            status="done",
            results_count=len(candidates),
            duration_ms=duration_ms,
        )

    @staticmethod
    def _deduplicate(candidates: list[CandidateProfile]) -> list[CandidateProfile]:
        """Remove duplicate candidates (same name or same github_url)."""
        seen_names: set[str] = set()
        seen_urls: set[str] = set()
        unique: list[CandidateProfile] = []
        for c in candidates:
            key = c.name.lower().strip()
            url  = (c.github_url or c.linkedin_url or "").lower()
            if key in seen_names or (url and url in seen_urls):
                continue
            seen_names.add(key)
            if url:
                seen_urls.add(url)
            unique.append(c)
        return unique
