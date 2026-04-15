# AeroAnalytics — AI Data Analyst

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black.svg)](https://flask.palletsprojects.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude-orange.svg)](https://aws.amazon.com/bedrock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Ask your airline data questions in plain English. A 4-node LangGraph AI pipeline converts your question to SQL, executes it, generates a business insight, and quality-reviews it — powered by Claude Haiku 4.5 on AWS Bedrock.

---

## What it does

Type a question in plain English. The LangGraph orchestration pipeline handles the rest — classifying your intent, fixing spelling mistakes, writing SQL, running it against the database, generating a business insight, and reviewing it for quality.

**Example questions:**
- *"Which airline has the best on-time performance?"*
- *"Show total revenue by cabin class"*
- *"Top 5 delay reasons this year"*
- *"Compare fuel costs by airline in 2024"*
- *"Show monthly passenger trend for Emirates"*
- *"Which route has the most cancellations?"*
- *"Top 10 busiest airports by flight count"*

---

## Architecture

```
Browser (HTML/CSS/JS + Chart.js)
        │  fetch() API calls
        ▼
Flask Server (flask_app/server.py)
        │
        └── LangGraph Orchestrator (agents/orchestrator.py)
                │
                ├── Node 1: Planner ────── Claude Haiku 4.5
                │   LLM reads question + schema, decides intent,
                │   maps non-airline words (patient→passenger),
                │   fuzzy preprocessing, query planning
                │
                ├── Node 2: SQL Generator ── Claude Haiku 4.5
                │   NL→SQL generation, execution,
                │   auto-retry on failure (max 2x)
                │
                ├── Node 3: Insight Generator ── Claude Haiku 4.5
                │   Results → business narrative
                │   Handles empty results gracefully
                │
                └── Node 4: Critic ────── Claude Haiku 4.5
                    Quality review: checks for numbers,
                    recommendations, and jargon-free language
                    Rewrites if needed
                        │
                ├── SQLite DB ─── airline_dummy.db (44,657 rows, 17 tables)
                └── PDF Generator ── ReportLab (with chart image)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Flask + Pure HTML/CSS/JavaScript |
| Charts | Chart.js 4 + chartjs-plugin-datalabels |
| Orchestration | LangGraph 1.1 (4-node pipeline) |
| LLM | Claude Haiku 4.5 via AWS Bedrock (Converse API) |
| Alt LLM | GPT-4o via Azure OpenAI |
| Database | SQLite · PostgreSQL · MySQL · CSV/Excel/JSON |
| PDF Reports | ReportLab (with chart screenshot) |
| Auth | Session-based login (DEV/PROD modes) |
| Deployment | AWS EC2 (Ubuntu, Gunicorn, systemd) |

---

## LangGraph Pipeline — 4 Nodes

```
[Planner] ──→ general/PII ──────────────────────────→ [END]
    │
    └──→ [SQL Generator] ──→ error (retry max 2x) ──→ [SQL Generator]
                │
                └──→ [Insight Generator]
                            │
                            └──→ [Critic] ──→ [END]
```

| Node | Role | LLM calls |
|---|---|---|
| Planner | LLM reads question + full schema, classifies intent, maps non-airline words to airline equivalents (patient→passenger), runs fuzzy preprocessing | 1 |
| SQL Generator | Writes SQL, executes it, retries with error context on failure | 1–3 |
| Insight Generator | Converts results to plain-English business narrative | 1 |
| Critic | Reviews insight quality, rewrites if needed | 1 |

---

## Airline Dataset — 44,657 rows · 17 tables

| Table | Rows | Description |
|---|---|---|
| flights | 3,000 | Delays, routes, fuel, revenue per flight |
| bookings | 8,000 | Cabin class, fares, channels |
| passengers | 5,000 | Nationality, loyalty tier, preferences |
| baggage | 6,299 | Weight, status (delivered/lost/delayed) |
| ground_services | 8,685 | Catering, fueling, handling |
| loyalty_transactions | 7,976 | Points earned and redeemed |
| financial_summary | 468 | Monthly P&L per airline |
| + 10 more | — | Airlines, airports, aircraft, routes, crew, maintenance, incidents, fuel |

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/shubhamsakhuja/aeroanalytics.git
cd aeroanalytics

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# Edit .env — add your AWS keys

# 5. Run
python flask_app/server.py
# Browser opens automatically at http://localhost:5000
```

**Windows — double-click:**
```
run_flask.bat
```

---

## Environment Variables (.env)

```properties
# ── App mode ─────────────────────────────────────────────
APP_ENV=dev              # dev = no login | prod = login required
APP_USERNAME=admin
APP_PASSWORD=aero2025

# ── AWS Bedrock ───────────────────────────────────────────
LLM_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-southeast-2

# Region prefixes: ap-southeast-2=au. | us-east-1=us. | eu-west-1=eu.
BEDROCK_MODEL_ID=au.anthropic.claude-haiku-4-5-20251001-v1:0

# ── Azure OpenAI (optional alternative LLM) ──────────────
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

---

## Project Structure

```
aeroanalytics/
│
├── flask_app/
│   ├── server.py                 Flask backend — all routes, auth, watchdog
│   └── templates/
│       ├── index.html            Full frontend (HTML/CSS/JS/Chart.js)
│       └── login.html            Login page (PROD mode)
│
├── agents/
│   ├── orchestrator.py           LangGraph 4-node pipeline (NEW)
│   ├── sql_agent.py              Fuzzy preprocessing helpers, PII detection (legacy fallback)
│   └── insight_agent.py          Fallback insight generator
│
├── connectors/
│   ├── router.py                 Routes to correct connector
│   ├── airline_demo.py           Airline DB + compact schema
│   ├── file_connector.py         CSV / Excel / JSON
│   ├── sqlite.py                 SQLite connector
│   ├── postgres.py               PostgreSQL connector
│   ├── mysql.py                  MySQL connector
│   └── bigquery.py               Google BigQuery connector
│
├── utils/
│   └── llm_provider.py           AWS Bedrock + Azure OpenAI client
│
├── reports/generator.py          PDF report builder (with chart image)
│
├── airline_dummy.db              44,657-row SQLite airline dataset
├── airline_db_generator.py       Regenerate the database
│
├── requirements.txt              All Python dependencies
├── .env.example                  Credential template
├── .env                          Your credentials (never commit)
├── .gitignore
│
├── run_flask.bat                 Windows launcher
├── run_flask.sh                  Mac/Linux launcher
│
├── README.md                     This file
├── DEPLOY.md                     EC2 deployment guide
└── Procfile                      Gunicorn startup command
```

---

## UI Features

| Feature | Detail |
|---|---|
| LangGraph pipeline | 4-node AI orchestration with retry, planning, and quality review |
| Natural language chat | Type any question — greetings and gibberish handled gracefully |
| Fuzzy logic | Fixes spelling mistakes, expands abbreviations, detects intent |
| PII protection | Two-layer block on personal data (question + SQL level) |
| SQL auto-retry | If SQL fails, LangGraph loops back with error context and retries |
| Bar chart | Labels above bar (≤10) or rotated inside bar (>10) |
| Line chart | Smooth curve, fills area, preserves chronological order |
| Pie / Doughnut | Top N slices + "Others", legend shows name + value + % |
| Top N selector | 5 / 10 / 15 / 20 / 50 / All — instant chart re-render |
| Date axis | YYYY-MM → "Jun / 2024" two-line format |
| PDF report | Chart screenshot (3x res) + insight + SQL + data table |
| CSV export | Full dataset download with smart filename from question |
| DEV / PROD mode | Toggle login requirement via APP_ENV in .env |
| Heartbeat watchdog | Server auto-shuts down after 10 min of no browser activity |

---

## Data Sources

| Source | How to connect |
|---|---|
| Airline Demo DB | Built-in, auto-connected on startup |
| Upload File | CSV, Excel (.xlsx/.xls), JSON |
| SQLite | Upload any .db file |
| PostgreSQL | Host, port, database, username, password |
| MySQL | Host, port, database, username, password |
| Google BigQuery | Upload service account JSON |

---

## Sample Questions

```
Flights & Operations
  Which airline has the best on-time performance?
  Top 5 most common delay reasons
  Which route has the most cancellations?
  Top 10 busiest airports by flight count

Revenue & Finance
  Show total revenue by cabin class
  Compare fuel costs by airline in 2024
  Which booking channel generates the most revenue?
  Monthly revenue trend for 2024

Passengers & Loyalty
  Passenger breakdown by nationality
  Loyalty tier distribution
  Average fare by loyalty tier
  Show monthly passenger trend for Emirates

Crew & Maintenance
  Which crew members have the most flight hours?
  Show maintenance logs by type
  List licenses expiring in the next 90 days

Safety
  Show all incidents by severity level
  Which routes have had the most incidents?
```

---

## Deployment

See **[DEPLOY.md](DEPLOY.md)** for the full EC2 step-by-step guide.

---

## Resume Description

> **AeroAnalytics — AI Data Analyst** | [GitHub](https://github.com/shubhamsakhuja/aeroanalytics)
>
> Full-stack AI analytics platform using a 4-node LangGraph orchestration pipeline (Planner → SQL Generator → Insight Generator → Critic) with Claude Haiku 4.5 on AWS Bedrock. The Planner node uses the LLM itself to classify intent and map any phrasing to the correct airline data — no hardcoded patterns. Features fuzzy NLP preprocessing, two-layer PII protection, SQL auto-retry, session auth (DEV/PROD modes), PDF report export with chart screenshot, and heartbeat-based auto-shutdown. Deployed on AWS EC2 with IAM role authentication.
>
> **Stack:** Python · Flask · LangGraph · AWS Bedrock (Claude Haiku 4.5) · SQLite · Chart.js · ReportLab · EC2

---

## License

MIT © 2026 Shubham Sakhuja
