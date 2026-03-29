"""
models.py — Pydantic data models for TalentRadar.

CandidateProfile : a single candidate from any source (DB, LinkedIn, GitHub).
ScoredCandidate  : a CandidateProfile with Gemini's score and explanation.
SearchRequest    : the recruiter's natural-language prompt payload.
ParsedRequirements: what Gemini extracts from the prompt.
SearchResponse   : the full API response returned to the frontend.
AgentStatus      : per-agent run metadata (how many results, time taken).
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class CandidateProfile(BaseModel):
    id: str
    name: str
    title: str                       # current job title
    location: str
    years_experience: int
    skills: List[str]
    focus_areas: List[str]
    bio: str
    linkedin_url: Optional[str] = None
    github_url: Optional[str]   = None
    github_username: Optional[str] = None
    email: Optional[str]        = None
    education: Optional[str]    = None
    current_company: Optional[str] = None
    avatar_url: Optional[str]   = None
    source: Literal["internal", "linkedin", "github"] = "internal"


class ScoredCandidate(BaseModel):
    profile: CandidateProfile
    score: int                       # 0–100
    explanation: str                 # Gemini's plain-English reasoning
    strengths: List[str]
    gaps: List[str]
    rank: int                        # 1–5


class ParsedRequirements(BaseModel):
    role: str
    skills: List[str]
    focus_areas: List[str]
    years_exp_min: int
    location: Optional[str] = None
    extra_notes: Optional[str] = None


class AgentStatus(BaseModel):
    name: str
    status: Literal["running", "done", "error"]
    results_count: int = 0
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class SearchRequest(BaseModel):
    prompt: str = Field(..., min_length=10, description="Recruiter's natural-language candidate description")


class SearchResponse(BaseModel):
    query_id: str
    prompt: str
    parsed_requirements: ParsedRequirements
    top_candidates: List[ScoredCandidate]
    agent_statuses: List[AgentStatus]
    total_candidates_evaluated: int
    duration_ms: float
