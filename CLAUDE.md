# CLAUDE.md — JobHunter Pro

> AI-powered remote job search automation for a fullstack backend-heavy developer based in Argentina.

## Project Identity

**Name:** JobHunter Pro
**Owner:** Tomas — fullstack backend developer (React, Smalltalk, Ruby on Rails, Go, Python, relational DBs)
**Target:** Remote positions paying $50–80k USD/year from US, EU, and global companies
**Location:** Olavarría, Buenos Aires, Argentina (UTC-3)
**Dev Time Budget:** 4–5 hours/day

---

## Architecture Philosophy

### API-First, Not Scrape-First

This project follows a **research-validated API-first strategy**. As of early 2026:

- Multiple remote job boards offer **free, stable public APIs** (RemoteOK, Himalayas, Remotive, Arbeitnow)
- LinkedIn and Wellfound have enterprise-grade anti-bot systems (DataDome, fingerprinting). Scraping them is legally risky (DMCA §1201 anti-circumvention theory in active litigation: Google v. SerpApi, Reddit v. Perplexity)
- SerpAPI's Google Jobs endpoint provides aggregated access to Indeed, LinkedIn, Glassdoor, ZipRecruiter listings for $75/month (5,000 searches) or 250 free/month
- Bypassing CAPTCHAs or bot detection is now potentially a **federal statutory violation** — avoid entirely

**Data Source Tiers (in order of priority):**

| Tier | Source | Method | Cost | Risk |
|------|--------|--------|------|------|
| 1 | RemoteOK | Public JSON API | Free | None |
| 1 | Himalayas | Public REST API + RSS | Free | None |
| 1 | Remotive | Public REST API + RSS | Free | None |
| 1 | Arbeitnow | Public REST API | Free | None |
| 1 | We Work Remotely | RSS feeds by category | Free | None |
| 2 | Jooble | Free REST API (key required) | Free | None |
| 2 | Adzuna | Free developer API (key required) | Free | None |
| 2 | SerpAPI Google Jobs | Paid API | $75/mo | None |
| 3 | HiringCafe | Light scraping (internal JSON API) | Free | Low |
| 3 | Working Nomads | Light scraping (undocumented API) | Free | Low |
| ❌ | LinkedIn | DO NOT SCRAPE | — | HIGH |
| ❌ | Wellfound | DO NOT SCRAPE (DataDome) | — | HIGH |
| ❌ | FlexJobs | DO NOT SCRAPE (paywall) | — | Medium |

### Legal Boundaries (Non-Negotiable)

- ✅ Use official APIs and RSS feeds
- ✅ Scrape only publicly visible data (anonymous, logged-out)
- ✅ Respect robots.txt
- ✅ Identify scraper honestly in User-Agent
- ✅ Implement reasonable rate limits
- ❌ NEVER create accounts to scrape
- ❌ NEVER bypass CAPTCHAs or bot detection
- ❌ NEVER disguise scraper identity (fake User-Agent, behavioral mimicry)
- ❌ NEVER scrape personal data (recruiter names, emails, profiles)
- ❌ NEVER use IP rotation to evade detection

---

## Tech Stack (Validated for 2026)

```
Runtime & Framework:
  Python 3.12+
  FastAPI (API + future web UI)
  Click (CLI interface)

Database:
  PostgreSQL 16 + pgvector (jobs + embeddings in one DB)
  Redis 7 (task queue, caching)
  Alembic (migrations)
  SQLAlchemy 2.0 (ORM, mapped_column syntax)

Data Collection:
  httpx (async HTTP client, HTTP/2)
  curl-cffi (stealth HTTP for sites needing browser TLS fingerprints)
  feedparser (RSS feeds)
  selectolax (HTML parsing — 5-30x faster than BeautifulSoup)
  Crawlee Python v1.0 (ONLY for Tier 3 scraping targets that need JS rendering)

AI & Matching:
  Anthropic Claude API (cover letters, resume tailoring, ATS analysis)
  BAAI/bge-base-en-v1.5 (local embeddings for job matching — 768 dims, MIT license)
  pgvector (vector similarity search in PostgreSQL)
  sentence-transformers 3.x (embedding framework)

Automation:
  Celery 5.x (task queue)
  Celery Beat (scheduling)

DevOps:
  Docker + docker-compose
  GitHub (version control)

Notifications:
  Email (smtplib or SendGrid)
  Telegram Bot API (optional)
```

### Why These Choices Over the Original Plan

| Original Plan | Updated Choice | Why |
|---|---|---|
| BeautifulSoup4 | selectolax (Lexbor) | 5-30x faster, handles malformed HTML |
| requests | httpx + curl-cffi | Async support, HTTP/2, browser TLS fingerprints |
| Playwright everywhere | Crawlee Python (only Tier 3) | Most sources are APIs/RSS — no browser needed |
| sentence-transformers all-MiniLM-L6-v2 | bge-base-en-v1.5 | Better quality, same speed class |
| Separate vector DB | pgvector in PostgreSQL | One DB for everything, hybrid queries |
| Scrapy | Crawlee Python v1.0 | Better Playwright integration, auto-resume, fingerprint rotation |

---

## Project Structure

```
jobhunter-pro/
├── CLAUDE.md                 # THIS FILE — project brain
├── .env.example
├── .env                      # git-ignored
├── .gitignore
├── README.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── Makefile
├── pyproject.toml
│
├── app/
│   ├── __init__.py
│   ├── config.py             # Pydantic Settings v2
│   ├── database.py           # SQLAlchemy engine, session, query helpers
│   ├── models.py             # ORM models (Job, Application, UserProfile, etc.)
│   │
│   ├── sources/              # Data collection — NOT called "scrapers"
│   │   ├── __init__.py
│   │   ├── base.py           # BaseSource ABC (normalize, deduplicate, save)
│   │   ├── remoteok.py       # Tier 1: JSON API
│   │   ├── himalayas.py      # Tier 1: REST API
│   │   ├── remotive.py       # Tier 1: REST API (2 req/min limit)
│   │   ├── arbeitnow.py      # Tier 1: REST API (no key)
│   │   ├── weworkremotely.py  # Tier 1: RSS feeds
│   │   ├── jooble.py         # Tier 2: REST API (key required)
│   │   ├── adzuna.py         # Tier 2: REST API (key required)
│   │   ├── serpapi_google.py  # Tier 2: Google Jobs via SerpAPI
│   │   ├── hiringcafe.py     # Tier 3: Light scraping
│   │   └── utils.py          # Salary parser, tag extractor, dedup
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── embeddings.py     # bge-base-en-v1.5 + pgvector operations
│   │   ├── matcher.py        # Job scoring (semantic + rule-based hybrid)
│   │   ├── cover_letter.py   # Claude API cover letter generation
│   │   ├── resume_tailor.py  # Claude API resume customization
│   │   ├── ats_checker.py    # ATS optimization analysis
│   │   └── prompts.py        # All prompt templates (centralized)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app
│   │   ├── dependencies.py
│   │   ├── schemas.py        # Pydantic request/response models
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── jobs.py
│   │       ├── applications.py
│   │       ├── profile.py
│   │       └── sources.py    # Trigger manual data collection
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py     # Celery config + beat schedule
│   │   ├── collection.py     # @task: daily_collect, etc.
│   │   ├── scoring.py        # @task: score_new_jobs, embed_new_jobs
│   │   └── notifications.py  # @task: daily_digest, telegram_alert
│   │
│   └── utils/
│       ├── __init__.py
│       ├── parsers.py        # Salary normalization, tag extraction
│       ├── validators.py     # Job data validation
│       └── logger.py         # Structured logging (structlog)
│
├── cli/
│   ├── __init__.py
│   └── commands.py           # Click CLI: review, apply, stats, collect, export
│
├── alembic/
│   ├── env.py
│   └── versions/
│
├── scripts/
│   ├── init_db.py
│   ├── seed_profile.py
│   ├── test_source.py        # Test individual data source
│   ├── collect_all.py        # Manual full collection run
│   └── export_data.py
│
├── tests/
│   ├── conftest.py
│   ├── test_sources.py
│   ├── test_ai.py
│   ├── test_models.py
│   └── fixtures/
│       └── sample_jobs.json
│
└── data/                     # git-ignored
    ├── resumes/
    ├── cover_letters/
    └── exports/
```

---

## Database Schema

### Key Design Decisions

- UUIDs as primary keys (portability, no sequence conflicts)
- pgvector `vector(768)` column on jobs table for embedding storage
- ARRAY types for tags/skills (PostgreSQL native)
- Timestamps with timezone everywhere
- Indexes on: source, scraped_at, match_score, status, embedding (ivfflat)

### Models

```
Job:
  id: UUID PK
  title: String(255) NOT NULL
  company: String(255) NOT NULL
  location: String(255)
  salary_min: Integer
  salary_max: Integer
  salary_currency: String(10) default 'USD'
  description: Text NOT NULL
  requirements: Text
  url: String(500) UNIQUE NOT NULL
  source: String(50)  -- 'remoteok', 'himalayas', 'serpapi_google', etc.
  posted_at: DateTime
  scraped_at: DateTime default now()
  is_remote: Boolean default True
  tags: ARRAY(String)  -- ['python', 'react', 'rails']
  embedding: Vector(768)  -- pgvector, nullable until scored
  match_score: Float  -- 0-100, nullable until scored
  status: Enum('new', 'reviewed', 'applied', 'rejected', 'interview', 'offer')
  notes: Text
  created_at: DateTime
  updated_at: DateTime

Application:
  id: UUID PK
  job_id: UUID FK -> jobs.id NOT NULL
  applied_at: DateTime default now()
  cover_letter: Text
  resume_version: String(255)  -- filepath
  status: Enum('applied', 'responded', 'interviewing', 'technical_test', 'offer', 'rejected')
  follow_up_date: Date
  interview_notes: Text
  notes: Text
  created_at, updated_at

PremiumPlatform:
  id: UUID PK
  platform: String(50)  -- 'turing', 'toptal', 'arc', 'revelo', 'tecla'
  vetting_status: Enum('pending', 'in_progress', 'approved', 'rejected')
  profile_url: String(500)
  applied_at: DateTime
  approved_at: DateTime
  test_score: Integer
  notes: Text
  created_at, updated_at

UserProfile (singleton):
  id: UUID PK
  full_name: String(255)
  email: String(255)
  phone: String(50)
  location: String(100)  -- 'Olavarría, Buenos Aires, Argentina'
  timezone: String(50)  -- 'America/Argentina/Buenos_Aires'
  linkedin_url: String(500)
  github_url: String(500)
  portfolio_url: String(500)
  primary_skills: ARRAY(String)  -- ['Ruby on Rails', 'Go', 'React', 'Smalltalk', 'Python', 'PostgreSQL']
  years_experience: Integer
  desired_salary_min: Integer  -- 50000
  desired_salary_max: Integer  -- 80000
  base_resume_path: String(500)
  base_cover_letter: Text
  languages: ARRAY(String)  -- ['Spanish (native)', 'English (fluent)']
  bio: Text
  created_at, updated_at
```

---

## Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://jobhunter:jobhunter123@localhost:5432/jobhunter_db

# Redis
REDIS_URL=redis://localhost:6379/0

# APIs — Tier 1 (free, no key needed)
# RemoteOK, Himalayas, Arbeitnow, WWR RSS = no keys needed

# APIs — Tier 2 (free, key required)
JOOBLE_API_KEY=
ADZUNA_APP_ID=
ADZUNA_API_KEY=
SERPAPI_KEY=                  # Optional: $75/mo for 5000 searches

# AI
ANTHROPIC_API_KEY=sk-ant-xxxxx

# User Settings
MIN_SALARY_USD=50000
MAX_SALARY_USD=80000
TARGET_ROLES=backend,fullstack,rails,ruby,go,golang,react,python,smalltalk,postgresql
TARGET_SENIORITY=mid,senior,lead

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_EMAIL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# App
ENV=development
DEBUG=True
LOG_LEVEL=INFO
```

---

## Data Source Implementation Details

### Tier 1: Free Public APIs

#### RemoteOK
```
Endpoint: GET https://remoteok.com/api
Auth: None
Format: JSON array (first item is metadata, skip it)
Rate limit: Undocumented, be reasonable (1 req/min)
Fields: position, company, location, salary_min, salary_max, description, tags[], url, date
Notes: Add "https://remoteok.com" prefix to relative URLs
```

#### Himalayas
```
Endpoint: GET https://himalayas.app/jobs/api
Params: limit (max 20), offset, category_slug
Auth: None
Rate limit: Returns 429 when exceeded
RSS: https://himalayas.app/rss (100 most recent)
MCP: https://mcp.himalayas.app/sse (for future AI agent integration)
Fields: title, company_name, salary_min/max, location_restrictions, timezone, description (HTML), application_url
Notes: Terms prohibit resubmitting to third-party aggregators (we're using for personal search, not republishing)
```

#### Remotive
```
Endpoint: GET https://remotive.com/api/remote-jobs
Params: category, search, limit
Categories endpoint: GET https://remotive.com/api/remote-jobs/categories
Auth: None
Rate limit: 2 requests/minute, max 4 requests/day recommended
RSS: https://remotive.com/remote-jobs/software-dev/feed
Fields: title, company_name, salary, description, url, publication_date, tags[], category
Notes: Public API jobs are delayed 24h from publication. RSS is more current.
```

#### Arbeitnow
```
Endpoint: GET https://www.arbeitnow.com/api/job-board-api
Auth: None (no key required)
Format: JSON with pagination
Fields: title, company_name, location, remote, description, tags[], url, created_at
Notes: Strong for European + remote jobs. Supports visa sponsorship filter.
```

#### We Work Remotely (RSS)
```
RSS feeds by category:
  https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss
  https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss
  https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss
  https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss
Auth: None
Format: RSS/XML (use feedparser)
Fields: title, company (in title usually), link, description (HTML), pubDate
Notes: Parse title format "Company: Job Title". Description is HTML, parse with selectolax.
LATAM-specific: https://weworkremotely.com/remote-latin-america-jobs (scrape or check for RSS)
```

### Tier 2: Free APIs with Key

#### Jooble
```
Endpoint: POST https://jooble.org/api/{API_KEY}
Body: { "keywords": "python rails", "location": "remote", "salary": "50000" }
Auth: API key in URL path (register at jooble.org/api/about)
Rate limit: Undocumented
Fields: title, company, location, salary, snippet, link, updated
```

#### Adzuna
```
Endpoint: GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
Params: app_id, app_key, what, where, salary_min, full_time, permanent
Auth: App ID + API key (register at developer.adzuna.com)
Countries: us, gb, de, fr, nl, au, ca, etc.
Fields: title, company, location, salary_min/max, description, redirect_url, created
Notes: Multi-country support. Run separate queries per country.
```

#### SerpAPI Google Jobs (Optional, Paid)
```
Endpoint: GET https://serpapi.com/search?engine=google_jobs
Params: q (query), location, chips (filters), api_key
Auth: API key
Rate limit: Based on plan (5000/mo on $75 plan)
Fields: title, company_name, location, description, extensions[], related_links[], detected_extensions (salary, schedule)
Notes: Aggregates from Indeed, LinkedIn, Glassdoor, ZipRecruiter, company pages. MOST COMPREHENSIVE single source.
```

### Tier 3: Light Scraping

#### HiringCafe
```
Internal API: Discovered via browser DevTools — returns structured JSON
Method: httpx with browser-like headers
Fields: title, description, requirements, company, compensation, location
Notes: No documented API. Internal search API returns good JSON. Refreshes 3x/day from 30K+ career pages. Minimal anti-bot.
Approach: Use curl-cffi, parse JSON response. If blocked, skip — not worth fighting.
```

---

## Job Matching Algorithm

### Hybrid Scoring (Semantic + Rules)

Total score: 0–100 points

```
A) Semantic Similarity (40 points):
   - Embed job description with bge-base-en-v1.5
   - Embed user profile (bio + skills summary)
   - Cosine similarity × 40
   - Store embedding in pgvector for future queries

B) Skills Match (30 points):
   - Extract required skills from job.requirements + job.description
   - Compare with profile.primary_skills
   - Exact match: full points per skill
   - Partial match (e.g., "Ruby" matches "Ruby on Rails"): 70% points
   - Formula: (matched_skills / total_required_skills) × 30

C) Salary Match (15 points):
   - job.salary_min >= profile.desired_salary_min: +15
   - Salary unknown: +10 (benefit of the doubt)
   - job.salary_max < profile.desired_salary_min: 0

D) Seniority Match (10 points):
   - Keywords: "senior", "lead", "principal", "staff" → senior job
   - Keywords: "junior", "entry", "intern" → junior job
   - Profile years >= 4 + senior job: +10
   - Mismatch (senior job, few years): +3
   - Junior job: +2

E) Location/Timezone Bonus (5 points):
   - "Remote" or "Anywhere": +5
   - "LATAM", "South America", "Argentina": +5
   - "Americas timezone", "UTC-3 to UTC-5": +4
   - "US timezone": +3
   - "EU only" or "US only" (no LATAM): +0
```

### pgvector Query Pattern

```sql
-- Hybrid query: relational filters + vector similarity
SELECT j.*,
       1 - (j.embedding <=> :query_embedding) as similarity
FROM jobs j
WHERE j.status = 'new'
  AND j.is_remote = true
  AND (j.salary_min >= :min_salary OR j.salary_min IS NULL)
ORDER BY j.match_score DESC NULLS LAST
LIMIT 20;
```

---

## AI Prompts (Centralized in app/ai/prompts.py)

### Cover Letter Generation

```
Model: claude-sonnet-4-20250514
Max tokens: 1000
Temperature: 0.7

System: You are a career coach helping a senior fullstack developer from Argentina
apply for remote positions. Write authentic, specific cover letters — not generic templates.

User prompt template:
---
Write a cover letter for this application:

**Job:** {title} at {company}
**Description:** {description_excerpt_500_chars}
**Key Requirements:** {top_5_requirements}

**Candidate:**
- Location: Olavarría, Argentina (UTC-3 — excellent overlap with US East/EU)
- Experience: {years} years in {skills_csv}
- Bio: {bio}
- Relevant experience highlights: {matched_experiences}

**Rules:**
1. 250-300 words, professional but warm
2. Open with something specific about the company or role — NOT "I am writing to express my interest"
3. Connect 2-3 specific skills/experiences to their requirements
4. Mention timezone advantage naturally (don't make it the focus)
5. Close with a clear next step
6. NO clichés: "passionate", "team player", "fast learner", "excited about this opportunity"
7. Plain text, ready to paste
---
```

### Resume Tailoring

```
Model: claude-sonnet-4-20250514
Max tokens: 1500
Temperature: 0.3 (more deterministic)

Task: Rewrite experience bullets to match job requirements.
Input: base resume sections + job requirements
Output: Rewritten bullets with relevant keywords naturally incorporated
Constraint: Keep truthful — enhance phrasing, don't invent experience
```

---

## Sprint Plan

### Sprint 0: Foundation (Day 1 — ~4h)

**Goal:** Project skeleton, Docker, database, config.

**Tasks:**
1. Create full folder structure with __init__.py files
2. Create .gitignore, .env.example, requirements.txt
3. Create docker-compose.yml (PostgreSQL 16 + pgvector extension, Redis 7)
4. Create app/config.py (Pydantic Settings v2)
5. Create app/models.py (all SQLAlchemy 2.0 models with pgvector)
6. Create app/database.py (engine, session, get_db dependency)
7. Setup Alembic, create initial migration
8. Create scripts/init_db.py + scripts/seed_profile.py
9. Verify: `docker-compose up -d`, `alembic upgrade head`, seed profile

**Verification:**
```bash
docker-compose ps  # postgres + redis running
python scripts/init_db.py  # tables created
python scripts/seed_profile.py  # profile seeded
psql -U jobhunter -d jobhunter_db -c "SELECT full_name FROM user_profiles;"
```

---

### Sprint 1: Tier 1 Data Sources (Day 2 — ~5h)

**Goal:** 5 free data sources collecting jobs into DB.

**Tasks:**
1. Create app/sources/base.py (BaseSource ABC with normalize, deduplicate, save)
2. Create app/utils/parsers.py (salary parser, tag extractor)
3. Implement in order (easiest first):
   - app/sources/remoteok.py (JSON API — simplest)
   - app/sources/arbeitnow.py (JSON API — no key)
   - app/sources/himalayas.py (REST API with pagination)
   - app/sources/weworkremotely.py (RSS with feedparser)
   - app/sources/remotive.py (REST API — respect 2 req/min)
4. Create scripts/test_source.py (test individual source)
5. Create scripts/collect_all.py (run all sources)
6. Deduplication logic in base.py (URL match + fuzzy title+company)

**Verification:**
```bash
python scripts/test_source.py remoteok --save  # should see 20-50 jobs
python scripts/collect_all.py  # all 5 sources, expect 100-200 jobs
psql ... -c "SELECT source, COUNT(*) FROM jobs GROUP BY source;"
```

---

### Sprint 2: Tier 2 Sources + CLI (Day 3 — ~5h)

**Goal:** Add keyed APIs, build CLI for daily use.

**Tasks:**
1. Implement app/sources/jooble.py (if key obtained)
2. Implement app/sources/adzuna.py (multi-country queries)
3. Implement app/sources/serpapi_google.py (if using paid plan)
4. Create cli/commands.py with Click:
   - `jobhunter collect [--source NAME | --all]`
   - `jobhunter stats` (jobs by source, by status, salary ranges, top tags)
   - `jobhunter review` (interactive: show top unreviewed jobs, mark status)
   - `jobhunter export [--format csv|json]`
5. Create Makefile with common commands

**Verification:**
```bash
jobhunter collect --all
jobhunter stats
jobhunter review  # interactive session
```

---

### Sprint 3: AI Matching Engine (Day 4–5 — ~8h total)

**Goal:** Semantic scoring + embedding storage.

**Tasks:**
1. Create app/ai/embeddings.py:
   - Load bge-base-en-v1.5 model
   - embed_text(text) → vector
   - embed_batch(texts) → vectors
   - Store in pgvector column
2. Create app/ai/matcher.py:
   - Hybrid scoring algorithm (semantic 40 + skills 30 + salary 15 + seniority 10 + location 5)
   - score_job(job, profile) → float
   - batch_score(jobs, profile) → sorted list
   - explain_score(job, profile) → breakdown dict
3. Add pgvector extension to migration:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ALTER TABLE jobs ADD COLUMN embedding vector(768);
   CREATE INDEX ON jobs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
   ```
4. Create app/tasks/scoring.py:
   - score_new_jobs() task
   - embed_new_jobs() task
5. Update CLI `jobhunter review` to show scores and sort by score

**Verification:**
```bash
python -c "from app.ai.matcher import JobMatcher; m = JobMatcher(); print(m.score_job(...))"
jobhunter review  # now shows [Score: 82] Title @ Company
```

---

### Sprint 4: AI Cover Letters + Apply Flow (Day 6–7 — ~8h total)

**Goal:** Generate personalized application materials with Claude.

**Tasks:**
1. Create app/ai/prompts.py (all prompt templates)
2. Create app/ai/cover_letter.py:
   - generate(job, profile) → cover letter text
   - Save to data/cover_letters/{job_id}.txt
3. Create app/ai/resume_tailor.py:
   - Parse base resume (PDF with pypdf or markdown)
   - quick_tailor(job, profile) → rewritten summary + bullets
4. Create app/ai/ats_checker.py:
   - check_resume(job, resume_text) → {ats_score, missing_keywords, suggestions}
5. Add CLI command:
   - `jobhunter apply <job_id> [--auto] [--dry-run]`
   - Interactive mode: generate CL → review → tailor resume → check ATS → save → mark applied
   - Auto mode: generate all, show preview, confirm, save
6. Create Application record in DB on apply

**Verification:**
```bash
jobhunter apply <job_id> --dry-run  # generates but doesn't save
jobhunter apply <job_id> --auto     # full flow
ls data/cover_letters/  # files created
```

---

### Sprint 5: Automation + Notifications (Day 8 — ~5h)

**Goal:** Hands-off daily operation.

**Tasks:**
1. Create app/tasks/celery_app.py:
   - Redis broker config
   - Beat schedule:
     - daily_collect: every day 02:00 ART
     - daily_embed_score: every day 03:00 ART
     - daily_digest: every day 09:00 ART
2. Create app/tasks/collection.py (daily_collect task)
3. Create app/tasks/notifications.py:
   - daily_digest: email with top 10 new matches (score > 70)
   - telegram_alert: instant notification for score > 90
4. Update docker-compose.yml:
   - Add celery-worker service
   - Add celery-beat service
   - Add flower service (port 5555, monitoring)
5. Create Dockerfile for the app

**Verification:**
```bash
docker-compose up -d  # all services including celery
# Wait for scheduled tasks or trigger manually:
python -c "from app.tasks.collection import daily_collect; daily_collect.delay()"
# Check flower at localhost:5555
```

---

### Sprint 6: Tier 3 Scraping + Polish (Day 9 — ~4h)

**Goal:** Add remaining sources, professional README.

**Tasks:**
1. Implement app/sources/hiringcafe.py (curl-cffi, JSON parsing)
2. Tests: test_sources.py, test_ai.py, test_models.py
3. Professional README.md for GitHub portfolio
4. scripts/backup_db.py (pg_dump wrapper)
5. scripts/cleanup_old_jobs.py (archive > 60 days)

---

### Sprint 7: FastAPI Dashboard (Day 10–12 — Optional)

**Goal:** Web UI for reviewing jobs.

**Tasks:**
1. FastAPI REST endpoints (jobs CRUD, applications, profile, trigger sources)
2. OpenAPI docs at /docs
3. Simple React frontend (or server-rendered with Jinja2 for speed)
4. Deploy to Railway or Fly.io free tier

---

## Parallel Track: Premium Platforms (Manual, During Week 1–2)

These require manual application — the system can track status in PremiumPlatform table.

| Platform | Action | Timeline | Notes |
|---|---|---|---|
| Arc.dev | Apply + vetting | Week 1 | Fastest approval, LATAM-friendly |
| Turing.com | Profile + skill tests | Week 1 | AI-based matching, automated vetting |
| Revelo | Register | Week 1 | 400K+ engineers, handles payroll/compliance |
| Tecla | Register | Week 1 | LATAM-focused, $60-80K range matches perfectly |
| Torre.ai | Complete profile | Week 1 | Colombian-founded, deep LATAM presence |
| Toptal | Study + apply | Week 2 | Harder vetting (algorithms + system design) |
| Lemon.io | Apply | Week 2 | LATAM-friendly, faster process |
| Gun.io | Apply | Week 2 | Similar to Toptal, less rigorous |
| GetOnBoard | Register | Week 1 | LATAM-native (Chile/Argentina/Colombia) |
| RubyOnRemote | Register + alerts | Week 1 | Perfect for Rails roles, 13K+ community |

---

## Coding Conventions

- Python 3.12+ features OK (match statements, type hints with `|` union)
- SQLAlchemy 2.0 syntax: `Mapped[str]`, `mapped_column()`
- Async where beneficial (httpx, Crawlee) but sync is fine for CLI/tasks
- Type hints on all function signatures
- Docstrings on all public classes/methods (Google style)
- structlog for logging (JSON structured output)
- `ruff` for linting and formatting
- Tests with pytest, fixtures in conftest.py
- Environment config via Pydantic Settings (never hardcode secrets)

---

## Cost Estimate

```
Required:
  Anthropic Claude API: ~$10-15/month (200-300 cover letters)
  Hosting (Railway free tier): $0
  Total minimum: ~$10-15/month

Optional:
  SerpAPI: $75/month (5,000 Google Jobs searches)
  Adzuna API: Free tier
  Domain: $12/year

Maximum: ~$90/month (with SerpAPI)
```

---

## Success Metrics

**Week 1:** 200+ jobs collected, system running daily, first application sent with AI materials
**Week 2:** 15+ applications, 2-3 screening calls, 1+ premium platform in progress
**Week 3-4:** 30+ applications total, 5-8 interviews, 1-2 technical assessments
**Month 2:** Offer(s) in the $50-80K range

---

## Key Reminders for Claude Code Sessions

1. **Always start from this file** — read CLAUDE.md at the beginning of each session
2. **API-first** — never default to scraping when an API exists
3. **Legal safety** — never bypass bot detection, never fake User-Agent
4. **Test each source independently** before integrating
5. **Commit frequently** — working increment per sprint
6. **Don't over-engineer** — CLI-first, web dashboard later
7. **Profile is fullstack backend-heavy** — prioritize Rails, Go, React, Smalltalk, Python jobs
8. **pgvector for everything** — no separate vector database
9. **selectolax, not BeautifulSoup** — for any HTML parsing
10. **httpx + curl-cffi, not requests** — for all HTTP
