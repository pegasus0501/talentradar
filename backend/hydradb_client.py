"""
hydradb_client.py — PostgreSQL/pgvector client for HydraDB.

HydraDB is a PostgreSQL-compatible database.  We use:
  - psycopg2        for the connection
  - pgvector        for storing and querying 768-dim embeddings
  - MOCK_MODE=true  to run fully in-memory (no HydraDB needed)

Tables created automatically on first connect:
  candidates  — stores all candidate profiles + their embedding vector
  search_sessions — caches search results for the UI

PLACEHOLDER: Set HYDRADB_CONNECTION_STRING in your .env file.
"""

import json
import os
import uuid
from typing import Any, Optional

from models import CandidateProfile

# ── Choose real vs mock ────────────────────────────────────────────────────────
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
CONNECTION_STRING = os.getenv(
    "HYDRADB_CONNECTION_STRING",
    "postgresql://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DB",
)

# In-memory store used when MOCK_MODE=true
_MOCK_STORE: list[dict] = []
_MOCK_SESSIONS: dict[str, Any] = {}


class HydraDBClient:
    """Thin wrapper around HydraDB (PostgreSQL + pgvector)."""

    def __init__(self) -> None:
        self._conn = None
        if not MOCK_MODE:
            self._connect()

    # ── Connection ─────────────────────────────────────────────────────────

    def _connect(self) -> None:
        import psycopg
        from pgvector.psycopg import register_vector

        self._conn = psycopg.connect(CONNECTION_STRING, autocommit=True)
        register_vector(self._conn)
        self._create_tables()

    def _cursor(self):
        return self._conn.cursor()

    def _create_tables(self) -> None:
        """Create tables + extensions if they don't exist."""
        with self._cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id            TEXT PRIMARY KEY,
                    name          TEXT,
                    title         TEXT,
                    location      TEXT,
                    years_experience INT,
                    skills        TEXT[],
                    focus_areas   TEXT[],
                    bio           TEXT,
                    linkedin_url  TEXT,
                    github_url    TEXT,
                    github_username TEXT,
                    email         TEXT,
                    education     TEXT,
                    current_company TEXT,
                    avatar_url    TEXT,
                    source        TEXT DEFAULT 'internal',
                    embedding     vector(768)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS search_sessions (
                    session_id TEXT PRIMARY KEY,
                    prompt     TEXT,
                    results    JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS candidates_embedding_idx
                ON candidates USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 10);
            """)

    def close(self) -> None:
        if self._conn:
            self._conn.close()

    # ── Candidates ─────────────────────────────────────────────────────────

    def insert_candidate(
        self,
        profile: dict,
        embedding: Optional[list[float]] = None,
    ) -> None:
        """Upsert a candidate. If embedding is None, skips vector column."""
        if MOCK_MODE:
            # Replace if same id
            _MOCK_STORE[:] = [c for c in _MOCK_STORE if c["id"] != profile["id"]]
            _MOCK_STORE.append({**profile, "embedding": embedding})
            return

        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO candidates
                    (id, name, title, location, years_experience, skills,
                     focus_areas, bio, linkedin_url, github_url, github_username,
                     email, education, current_company, avatar_url, source, embedding)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    name=EXCLUDED.name, title=EXCLUDED.title,
                    skills=EXCLUDED.skills, embedding=EXCLUDED.embedding;
                """,
                (
                    profile["id"],
                    profile.get("name"),
                    profile.get("title"),
                    profile.get("location"),
                    profile.get("years_experience", 0),
                    profile.get("skills", []),
                    profile.get("focus_areas", []),
                    profile.get("bio", ""),
                    profile.get("linkedin_url"),
                    profile.get("github_url"),
                    profile.get("github_username"),
                    profile.get("email"),
                    profile.get("education"),
                    profile.get("current_company"),
                    profile.get("avatar_url"),
                    profile.get("source", "internal"),
                    embedding,
                ),
            )

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 20,
        source_filter: Optional[str] = None,
    ) -> list[CandidateProfile]:
        """Return top_k candidates by cosine similarity to query_embedding."""
        if MOCK_MODE:
            import numpy as np

            q = np.array(query_embedding)
            scored: list[tuple[float, dict]] = []
            for c in _MOCK_STORE:
                emb = c.get("embedding")
                if emb is None:
                    continue
                e = np.array(emb)
                sim = float(np.dot(q, e) / (np.linalg.norm(q) * np.linalg.norm(e) + 1e-9))
                if source_filter is None or c.get("source") == source_filter:
                    scored.append((sim, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [self._row_to_profile(c) for _, c in scored[:top_k]]

        source_clause = "AND source = %s" if source_filter else ""
        params: tuple = (query_embedding, top_k)
        if source_filter:
            params = (query_embedding, source_filter, top_k)

        with self._cursor() as cur:
            cur.execute(
                f"""
                SELECT id, name, title, location, years_experience, skills,
                       focus_areas, bio, linkedin_url, github_url, github_username,
                       email, education, current_company, avatar_url, source
                FROM candidates
                WHERE embedding IS NOT NULL {source_clause}
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (query_embedding,) + ((source_filter,) if source_filter else ()) + (top_k,),
            )
            rows = cur.fetchall()
        return [self._row_to_profile(dict(zip(self._candidate_cols(), r))) for r in rows]

    def get_all_candidates(
        self,
        limit: int = 100,
        source: Optional[str] = None,
    ) -> list[CandidateProfile]:
        """Return all candidates (used for fallback keyword search)."""
        if MOCK_MODE:
            results = _MOCK_STORE if source is None else [c for c in _MOCK_STORE if c.get("source") == source]
            return [self._row_to_profile(c) for c in results[:limit]]

        with self._cursor() as cur:
            if source:
                cur.execute("SELECT * FROM candidates WHERE source=%s LIMIT %s;", (source, limit))
            else:
                cur.execute("SELECT * FROM candidates LIMIT %s;", (limit,))
            rows = cur.fetchall()
        return [self._row_to_profile(dict(zip(self._candidate_cols(), r))) for r in rows]

    def count_candidates(self) -> int:
        if MOCK_MODE:
            return len(_MOCK_STORE)
        with self._cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM candidates;")
            return cur.fetchone()[0]

    # ── Sessions ───────────────────────────────────────────────────────────

    def save_session(self, session_id: str, prompt: str, results: dict) -> None:
        if MOCK_MODE:
            _MOCK_SESSIONS[session_id] = {"prompt": prompt, "results": results}
            return
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO search_sessions (session_id, prompt, results) VALUES (%s,%s,%s) ON CONFLICT (session_id) DO NOTHING;",
                (session_id, prompt, json.dumps(results)),
            )

    def get_session(self, session_id: str) -> Optional[dict]:
        if MOCK_MODE:
            return _MOCK_SESSIONS.get(session_id)
        with self._cursor() as cur:
            cur.execute("SELECT prompt, results FROM search_sessions WHERE session_id=%s;", (session_id,))
            row = cur.fetchone()
        if not row:
            return None
        return {"prompt": row[0], "results": row[1]}

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _candidate_cols() -> list[str]:
        return [
            "id", "name", "title", "location", "years_experience", "skills",
            "focus_areas", "bio", "linkedin_url", "github_url", "github_username",
            "email", "education", "current_company", "avatar_url", "source",
        ]

    @staticmethod
    def _row_to_profile(row: dict) -> CandidateProfile:
        return CandidateProfile(
            id=row.get("id", str(uuid.uuid4())),
            name=row.get("name", "Unknown"),
            title=row.get("title", "Engineer"),
            location=row.get("location", "Remote"),
            years_experience=int(row.get("years_experience", 0)),
            skills=row.get("skills") or [],
            focus_areas=row.get("focus_areas") or [],
            bio=row.get("bio", ""),
            linkedin_url=row.get("linkedin_url"),
            github_url=row.get("github_url"),
            github_username=row.get("github_username"),
            email=row.get("email"),
            education=row.get("education"),
            current_company=row.get("current_company"),
            avatar_url=row.get("avatar_url"),
            source=row.get("source", "internal"),  # type: ignore
        )
