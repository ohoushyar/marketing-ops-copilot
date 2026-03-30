# Marketing Ops Copilot

A CLI-first Marketing Ops Copilot that combines:

- **Docs RAG** (Markdown-only) with **Ollama** + **Postgres/pgvector**
- **Deterministic analytics** (pandas) over offline **CSV exports**
- An **LLM tool-using investigation** endpoint (`/analytics/investigate`) that plans analysis steps but only reports numbers produced by tools

## What this is (and isn’t)

### This is
- A lightweight “copilot” you can run locally
- Grounded Q&A over internal docs (UTM policy, SOPs, etc.)
- Repeatable KPI computation and week-over-week analysis from CSV exports
- An investigation workflow where the LLM selects *which* analytics tools to run, but the tools compute the results

### This is not
- A full production system (no auth, no permissions model)
- A replacement for your BI stack
- An LLM that’s allowed to invent metrics

---

## Requirements
- Docker
- Python **3.11+**
- (Optional) `make`
- Internet access the first time you pull models

---

## Quickstart

### 1) Start dependencies
```bash
make up
```

Pull models inside the Ollama container:
```bash
make pull-models
```

### 2) Create and activate a virtualenv
```bash
make venv
```

### 3) Run the API
```bash
make dev
```

Health check:
```bash
curl http://localhost:8000/health
```

### 4) Run the full demo
In a second terminal, with the API already running:

```bash
make demo
```

This will:
- generate mock analytics data
- ingest docs from `docs/`
- ask a sample RAG question
- run a sample investigation over the generated data

---

## Docs RAG (Markdown-only)

### Add docs
Put Markdown files under `docs/` (example files you can create):
- `docs/docs_utm_policy.md`
- `docs/docs_weekly_reporting_sop.md`
- `docs/docs_budget_change_process.md`

### Ingest docs
```bash
make ingest
```

### Ask questions
```bash
copilot ask "What UTMs are required and what formatting rules do we follow?" --citations
```

If the answer is not present in docs, the assistant should refuse and ask a clarifying question.

---

## Analytics (CSV exports)

### Data format
Create these files under `data/`:

- `data/spend.csv` with columns: `date,campaign,spend` (optional: `channel`)
- `data/clicks.csv` with columns: `date,campaign,clicks,impressions`
- `data/conversions.csv` with columns: `date,campaign,conversions,revenue`

**Important:** In this project, `conversions` is a generic post-click event count (e.g., leads, signups, purchases). KPIs interpret it accordingly.

### Generate mock data (optional)
```bash
python scripts/generate_mock_data.py
```

### Weekly KPIs
```bash
copilot kpi --week 2026-03-16 --by campaign
```

Equivalent Makefile wrapper:
```bash
make kpi WEEK=2026-03-16
```

---

## Investigations (LLM + tools, grounded)

`copilot investigate` calls the API endpoint `POST /analytics/investigate`.

- The **LLM plans** which tools to run (weekly KPIs, deltas, top movers)
- The API **executes** the tools deterministically (pandas)
- The response includes:
  - `answer` (narrative)
  - `tool_runs` (tables used as evidence)
  - `run_id` (logged in Postgres)

### Example
```bash
copilot investigate "Why did CAC rise last week? Identify the worst campaigns." --week 2026-03-16
```

Makefile wrapper:
```bash
make investigate WEEK=2026-03-16 Q="Why did CAC rise last week?"
```

---

## Endpoints (high level)
- `GET /health`
- `POST /ingest`
- `POST /chat`
- `POST /analytics/weekly_kpis`
- `POST /analytics/kpi_delta`
- `POST /analytics/top_movers`
- `POST /analytics/investigate`

---

## Development

### Lint / format / test
```bash
make lint
make fmt
make test
```

### Eval (optional, if you added Day 5)
```bash
make eval
```

---

## Notes on persistence
- Vector embeddings + runs are stored in Postgres (pgvector).
- Tool outputs are **summarized** when logged (to avoid storing very large tables).

---

## Troubleshooting

### Ollama errors
If the API returns `502` during `/chat` or `/analytics/investigate`:
- confirm Ollama container is running: `docker compose ps`
- list models: `curl http://localhost:11434/api/tags`
- pull models again:
  - `docker compose exec ollama ollama pull llama3.1:8b`
  - `docker compose exec ollama ollama pull nomic-embed-text`

### CSV schema errors
If analytics endpoints fail, ensure required columns exist:
- spend: `date,campaign,spend`
- clicks: `date,campaign,clicks,impressions`
