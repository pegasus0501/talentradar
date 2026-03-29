"""
agents/scorer.py — Gemini-powered Candidate Scoring & Ranking Agent.

What it does:
  1. Receives the merged candidate pool (up to ~30–40 profiles) from
     the three search agents.
  2. Sends all profiles to Gemini in a single structured prompt asking
     for a 0-100 score and plain-English reasoning per candidate.
  3. Joins the scores back to the original CandidateProfile objects.
  4. Returns the top top_k as ScoredCandidate objects, ranked 1–5.

Design note:
  We send all candidates in one LLM call rather than N calls to:
    a) Reduce latency (one round-trip vs 30)
    b) Let Gemini make relative comparisons across candidates
    c) Keep costs low during a hackathon
"""

import asyncio
from models import CandidateProfile, ParsedRequirements, ScoredCandidate
from gemini_client import GeminiClient


class ScorerAgent:
    def __init__(self, gemini: GeminiClient) -> None:
        self._gemini = gemini

    async def rank(
        self,
        requirements: ParsedRequirements,
        candidates: list[CandidateProfile],
        top_k: int = 5,
    ) -> list[ScoredCandidate]:
        if not candidates:
            return []

        loop = asyncio.get_event_loop()

        # Run the synchronous Gemini call in a thread pool
        scored_dicts = await loop.run_in_executor(
            None,
            self._gemini.score_candidates,
            requirements,
            candidates,
        )

        # Build a lookup {candidate_id → CandidateProfile}
        profile_map = {c.id: c for c in candidates}

        scored: list[ScoredCandidate] = []
        for i, s in enumerate(scored_dicts[:top_k]):
            cid = s.get("id", "")
            profile = profile_map.get(cid)
            if profile is None:
                continue
            scored.append(
                ScoredCandidate(
                    profile=profile,
                    score=int(s.get("score", 50)),
                    explanation=s.get("explanation", "No explanation provided."),
                    strengths=s.get("strengths", []),
                    gaps=s.get("gaps", []),
                    rank=i + 1,
                )
            )

        return scored
