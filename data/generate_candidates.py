"""
data/generate_candidates.py — Synthetic candidate data generator + HydraDB seeder.

What this script does:
  1. Generates 100 realistic engineer profiles using Faker + custom tech data.
     - 60 "internal" company database candidates
     - 40 synthetic "LinkedIn" profiles (stored in HydraDB as source='linkedin')
  2. Embeds each profile bio using Gemini text-embedding-004.
  3. Upserts all profiles into HydraDB.

Run once before starting the app:
    cd GMI
    python data/generate_candidates.py

Prerequisites:
    pip install faker google-genai psycopg[binary] pgvector python-dotenv
    GEMINI_API_KEY and HYDRADB_CONNECTION_STRING must be set in ../.env
"""

import os
import sys
import random
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from faker import Faker
from gemini_client import GeminiClient
from hydradb_client import HydraDBClient

fake = Faker()
random.seed(42)

# ── Realistic tech data pools ──────────────────────────────────────────────────

TITLES = [
    "Software Engineer", "Senior Software Engineer", "Staff Engineer",
    "Principal Engineer", "ML Engineer", "Senior ML Engineer",
    "Platform Engineer", "Site Reliability Engineer", "Backend Engineer",
    "Distributed Systems Engineer", "AI Research Engineer", "Data Engineer",
    "Full Stack Engineer", "DevOps Engineer", "Cloud Architect",
]

COMPANIES = [
    "Google", "Meta", "Apple", "Amazon", "Microsoft", "OpenAI", "Anthropic",
    "Scale AI", "Databricks", "Snowflake", "Stripe", "Airbnb", "Uber",
    "Lyft", "DoorDash", "Instacart", "Figma", "Notion", "Linear",
    "Vercel", "Cloudflare", "HashiCorp", "Datadog", "PagerDuty",
    "Confluent", "Palantir", "Anduril", "Shield AI", "Waymo",
]

SCHOOLS = [
    "Stanford University", "MIT", "UC Berkeley", "Carnegie Mellon University",
    "Georgia Tech", "University of Michigan", "Caltech", "Cornell University",
    "University of Washington", "UT Austin", "UCLA", "University of Illinois",
]

DEGREES = ["B.S. Computer Science", "M.S. Computer Science", "Ph.D. Computer Science",
           "B.S. Electrical Engineering", "M.S. Machine Learning"]

SKILLS_POOL = [
    "Python", "Go", "Rust", "Java", "C++", "TypeScript", "Scala",
    "Kubernetes", "Docker", "Terraform", "Helm", "AWS", "GCP", "Azure",
    "PostgreSQL", "Redis", "Kafka", "Spark", "Flink", "Airflow",
    "PyTorch", "TensorFlow", "JAX", "scikit-learn", "Hugging Face",
    "gRPC", "GraphQL", "REST APIs", "Microservices", "LangChain",
    "Ray", "Dask", "ClickHouse", "Elasticsearch", "Prometheus", "Grafana",
]

FOCUS_AREAS_POOL = [
    "Distributed Systems", "AI/ML", "MLOps", "LLM Inference",
    "Data Infrastructure", "Real-Time Systems", "Cloud Infrastructure",
    "Platform Engineering", "Backend Services", "Recommendation Systems",
    "Search & Retrieval", "Natural Language Processing", "Computer Vision",
    "Autonomous Systems", "High-Performance Computing", "Edge Computing",
]

LOCATIONS = [
    "San Francisco, CA", "San Francisco, CA", "San Francisco, CA",  # weighted
    "New York, NY", "Seattle, WA", "Austin, TX",
    "Los Angeles, CA", "Boston, MA", "Chicago, IL", "Denver, CO",
    "Remote", "London, UK", "Toronto, Canada",
]

BIO_TEMPLATES = [
    "{years}+ year {title} specialising in {focus1} and {focus2}. "
    "Previously at {company}, now building {project}. "
    "Passionate about {passion}.",

    "I build {focus1} systems that scale. "
    "{years} years of experience across {skill1}, {skill2}, and {skill3}. "
    "Ex-{company}. Based in {location}.",

    "Software engineer with a focus on {focus1}. "
    "I've shipped production systems handling millions of events/sec. "
    "Strong background in {skill1} and {skill2}. "
    "Open source contributor.",

    "Backend & {focus1} engineer. {years} years professional experience. "
    "B.S./M.S. from a top school. Previously at {company}. "
    "Interested in {focus2} and {skill1}.",
]

PROJECTS = [
    "scalable inference pipelines", "a distributed KV store",
    "real-time ML feature platforms", "multi-tenant SaaS infrastructure",
    "low-latency trading systems", "autonomous agent frameworks",
    "vector search engines", "streaming data pipelines",
]

PASSIONS = [
    "developer experience", "systems performance", "open-source tooling",
    "making AI accessible", "reliability engineering",
    "building with Rust", "distributed databases", "LLM fine-tuning",
]


# ── Generator ──────────────────────────────────────────────────────────────────

def _generate_profile(source: str) -> dict:
    skills = random.sample(SKILLS_POOL, k=random.randint(5, 9))
    focus  = random.sample(FOCUS_AREAS_POOL, k=random.randint(2, 3))
    years  = random.randint(1, 15)
    title  = random.choice(TITLES)
    company = random.choice(COMPANIES)
    location = random.choice(LOCATIONS)
    school   = random.choice(SCHOOLS)
    degree   = random.choice(DEGREES)

    bio_tmpl = random.choice(BIO_TEMPLATES)
    bio = bio_tmpl.format(
        years=years,
        title=title,
        focus1=focus[0],
        focus2=focus[1] if len(focus) > 1 else focus[0],
        company=company,
        project=random.choice(PROJECTS),
        passion=random.choice(PASSIONS),
        skill1=skills[0],
        skill2=skills[1],
        skill3=skills[2],
        location=location,
    )

    first_name = fake.first_name()
    last_name  = fake.last_name()
    username   = f"{first_name.lower()}{last_name.lower()}{random.randint(1,99)}"

    return {
        "id": str(uuid.uuid4()),
        "name": f"{first_name} {last_name}",
        "title": title,
        "location": location,
        "years_experience": years,
        "skills": skills,
        "focus_areas": focus,
        "bio": bio,
        "linkedin_url": f"https://linkedin.com/in/{username}" if source == "linkedin" else None,
        "github_url": f"https://github.com/{username}" if source == "internal" else None,
        "github_username": username if source == "internal" else None,
        "email": f"{username}@{fake.free_email_domain()}",
        "education": f"{degree}, {school}",
        "current_company": company,
        "avatar_url": f"https://api.dicebear.com/8.x/avataaars/svg?seed={username}",
        "source": source,
    }


def seed(n_internal: int = 60, n_linkedin: int = 40) -> None:
    print("🚀 TalentRadar — Synthetic Data Seeder")
    print(f"   Generating {n_internal} internal + {n_linkedin} LinkedIn profiles...")

    gemini = GeminiClient()
    db = HydraDBClient()

    profiles = (
        [_generate_profile("internal") for _ in range(n_internal)]
        + [_generate_profile("linkedin") for _ in range(n_linkedin)]
    )

    for i, p in enumerate(profiles, 1):
        # Build a text representation for embedding
        embed_text = (
            f"{p['title']} {' '.join(p['skills'])} "
            f"{' '.join(p['focus_areas'])} {p['bio']} {p['location']}"
        )
        try:
            embedding = gemini.embed_text(embed_text)
        except Exception as e:
            print(f"   ⚠  Embedding failed for {p['name']}: {e}. Using None.")
            embedding = None

        db.insert_candidate(p, embedding)

        if i % 10 == 0:
            print(f"   ✓  {i}/{len(profiles)} profiles seeded")

    total = db.count_candidates()
    print(f"\n✅ Done! HydraDB now contains {total} candidate profiles.")


if __name__ == "__main__":
    seed()
