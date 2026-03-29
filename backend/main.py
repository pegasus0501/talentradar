"""
main.py — FastAPI application entry point.

Endpoints
---------
GET  /              → health check
GET  /api/health    → health + candidate count
POST /api/search    → main search pipeline (runs all 3 agents)
GET  /api/candidates→ list candidates from HydraDB (paginated)
GET  /api/session/{id} → retrieve cached search result

CORS is configured to allow the Vite dev server (localhost:5173).

Run with:
    uvicorn main:app --reload --port 8000
"""

import asyncio
import os
import sys
import random
import uuid

sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from models import SearchRequest, SearchResponse, CandidateProfile
from hydradb_client import HydraDBClient, MOCK_MODE
from agents import OrchestratorAgent


def _generate_mock_profiles(n_internal=60, n_linkedin=40):
    from faker import Faker
    fake = Faker(); random.seed(42)
    TITLES = ["Software Engineer","Senior Software Engineer","Staff Engineer","ML Engineer",
              "Distributed Systems Engineer","AI Research Engineer","Platform Engineer",
              "Backend Engineer","Senior ML Engineer","Principal Engineer"]
    COMPANIES = ["Google","Meta","OpenAI","Anthropic","Scale AI","Databricks","Snowflake",
                 "Stripe","Airbnb","Uber","Cloudflare","Vercel","Confluent","Palantir"]
    SKILLS_POOL = ["Python","Go","Rust","Java","Kubernetes","Docker","Kafka","Spark",
                   "PyTorch","TensorFlow","gRPC","Redis","Postgres","AWS","GCP",
                   "LangChain","Ray","Elasticsearch","Prometheus","TypeScript"]
    FOCUS_POOL = ["Distributed Systems","AI/ML","MLOps","LLM Inference","Data Infrastructure",
                  "Real-Time Systems","Cloud Infrastructure","Platform Engineering",
                  "NLP","Recommendation Systems","Search & Retrieval","Computer Vision"]
    LOCATIONS = ["San Francisco, CA","San Francisco, CA","New York, NY","Seattle, WA",
                 "Austin, TX","Remote","Los Angeles, CA","Boston, MA"]
    profiles = []
    for source in (["internal"] * n_internal + ["linkedin"] * n_linkedin):
        fn, ln = fake.first_name(), fake.last_name()
        uname = f"{fn.lower()}{ln.lower()}{random.randint(1,99)}"
        skills = random.sample(SKILLS_POOL, k=random.randint(5, 9))
        focus  = random.sample(FOCUS_POOL, k=random.randint(2, 3))
        years  = random.randint(1, 15)
        company = random.choice(COMPANIES)
        location = random.choice(LOCATIONS)
        profiles.append({
            "id": str(uuid.uuid4()),
            "name": f"{fn} {ln}",
            "title": random.choice(TITLES),
            "location": location,
            "years_experience": years,
            "skills": skills,
            "focus_areas": focus,
            "bio": (f"{years}+ year engineer specialising in {focus[0]}"
                    f"{' and '+focus[1] if len(focus)>1 else ''}. "
                    f"Previously at {company}. Strong in {skills[0]}, {skills[1]}."),
            "linkedin_url": f"https://linkedin.com/in/{uname}" if source == "linkedin" else None,
            "github_url": f"https://github.com/{uname}" if source == "internal" else None,
            "github_username": uname if source == "internal" else None,
            "email": f"{uname}@example.com",
            "education": f"B.S. CS, {random.choice(['Stanford','MIT','UC Berkeley','CMU','Georgia Tech'])}",
            "current_company": company,
            "avatar_url": f"https://api.dicebear.com/8.x/avataaars/svg?seed={uname}",
            "source": source,
        })
    return profiles


db = HydraDBClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if MOCK_MODE and db.count_candidates() == 0:
        print("🌱 MOCK_MODE: Seeding 100 synthetic candidates into memory...")
        for p in _generate_mock_profiles():
            db.insert_candidate(p, embedding=None)
        print(f"✅ Seeded {db.count_candidates()} candidates.")
    yield


app = FastAPI(
    title="TalentRadar API",
    description="Multi-agent HR candidate search powered by Gemini + HydraDB",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "TalentRadar API"}


@app.get("/api/health", tags=["Health"])
async def health():
    try:
        count = db.count_candidates()
        return {"status": "ok", "candidates_in_db": count}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest):
    """
    Main search endpoint.

    1. Parses the recruiter prompt with Gemini.
    2. Launches HydraDB, GitHub, and LinkedIn agents in parallel.
    3. Scores and ranks the merged pool with Gemini.
    4. Returns the top-5 ScoredCandidates + agent metadata.
    """
    orchestrator = OrchestratorAgent()

    (
        query_id,
        requirements,
        top5,
        statuses,
        total_evaluated,
        duration_ms,
    ) = await orchestrator.run(request.prompt)

    return SearchResponse(
        query_id=query_id,
        prompt=request.prompt,
        parsed_requirements=requirements,
        top_candidates=top5,
        agent_statuses=statuses,
        total_candidates_evaluated=total_evaluated,
        duration_ms=round(duration_ms, 1),
    )


@app.get("/api/candidates", response_model=list[CandidateProfile], tags=["Candidates"])
async def list_candidates(limit: int = 50, source: str | None = None):
    """Returns candidates stored in HydraDB (paginated)."""
    try:
        return db.get_all_candidates(limit=limit, source=source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """Returns a cached search session result."""
    data = db.get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data
