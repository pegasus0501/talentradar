# 🎯 TalentRadar — AI-Powered HR Talent Search

> Multi-agent talent acquisition system for recruiters. Describe your ideal candidate in plain English → get the top 5 matches from your internal database, LinkedIn, and GitHub — powered by Gemini AI + HydraDB.

---

## 🔑 API Keys Required

| Key | Where to get it | .env variable |
|---|---|---|
| **Gemini API Key** | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | `GEMINI_API_KEY` |
| **HydraDB Connection** | Your HydraDB dashboard | `HYDRADB_CONNECTION_STRING` |
| **GitHub Token** _(optional)_ | [github.com/settings/tokens](https://github.com/settings/tokens) | `GITHUB_TOKEN` |

---

## 🗂 Project Structure

```
GMI/
├── backend/
│   ├── main.py              # FastAPI server (entry point)
│   ├── models.py            # All Pydantic data models
│   ├── gemini_client.py     # Gemini API wrapper (parsing + scoring + embeddings)
│   ├── hydradb_client.py    # HydraDB/PostgreSQL + pgvector client
│   ├── requirements.txt
│   └── agents/
│       ├── orchestrator.py  # Master agent — runs all 3 in parallel
│       ├── hydradb_agent.py # Agent 1: vector search internal DB
│       ├── github_agent.py  # Agent 2: GitHub REST API search
│       ├── linkedin_agent.py# Agent 3: LinkedIn profiles (synthetic fallback)
│       └── scorer.py        # Gemini ranking agent (0-100 scores)
├── data/
│   └── generate_candidates.py  # Generates + seeds 100 synthetic profiles
├── frontend/
│   ├── src/
│   │   ├── pages/Home.jsx       # Recruiter prompt input page
│   │   ├── pages/Results.jsx    # Top-5 results page
│   │   └── components/
│   │       ├── PromptInput.jsx  # Search textarea + example chips
│   │       ├── AgentStatus.jsx  # 3-agent status cards
│   │       ├── CandidateCard.jsx# Ranked candidate card with score ring
│   │       └── TopFiveGrid.jsx  # Results layout grid
│   └── index.html
└── .env.example
```

---

## 🚀 Setup & Run

### 1. Configure API Keys
```bash
cd GMI
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY and HYDRADB_CONNECTION_STRING
```

### 2. Install Backend
```bash
cd backend
pip install -r requirements.txt
```

### 3. Seed the Database (100 synthetic candidates)
```bash
cd GMI
python data/generate_candidates.py
```

### 4. Start Backend
```bash
cd GMI/backend
uvicorn main:app --reload --port 8000
```

### 5. Start Frontend
```bash
cd GMI/frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## 🏗 How It Works

```
Recruiter types: "Software engineer, distributed systems, 3+ yrs, AI/ML, SF"
                                    ↓
                    Gemini parses → structured requirements
                                    ↓
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                      ▼
    Agent 1: HydraDB         Agent 2: GitHub         Agent 3: LinkedIn
    (vector search)          (REST API)              (synthetic profiles)
    ~10-20 candidates        ~5-10 developers        ~10-15 profiles
              └─────────────────────┼──────────────────────┘
                                    ▼
                        Merge + deduplicate (~35 candidates)
                                    ▼
                    Gemini scores each 0-100 in one call
                                    ▼
                         Top 5 returned to UI
```

---

## 🌟 Tech Stack

| Layer | Technology |
|---|---|
| AI / LLM | Google Gemini 1.5 Pro |
| Embeddings | Gemini text-embedding-004 |
| Database | HydraDB (PostgreSQL + pgvector) |
| Backend | FastAPI + Python asyncio |
| Frontend | Vite + React + React Router |
| GitHub Search | GitHub REST API v3 |

---

## 📝 No HydraDB? Use Mock Mode

Set `MOCK_MODE=true` in `.env` to run with an in-memory store (no database needed). The seeded profiles will be held in memory for the session.




https://github.com/user-attachments/assets/55d80e35-67dd-4edd-a105-3ec0ac7fcb88


