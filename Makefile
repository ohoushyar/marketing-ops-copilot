SHELL := /bin/bash

PY ?= python
VENV ?= .ai-py313
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
COPILOT := $(VENV)/bin/copilot
RUFF := $(VENV)/bin/ruff
PYTEST := $(VENV)/bin/pytest

export PYTHONPATH := .

.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  make venv            Create venv and install deps"
	@echo "  make dev             Run API with reload"
	@echo "  make up              Start docker services (postgres+ollama)"
	@echo "  make down            Stop docker services"
	@echo "  make pull-models     Pull ollama chat + embed models"
	@echo "  make ingest          Ingest ./docs into vector store"
	@echo "  make ask Q='...'     Ask a question (use C=1 for citations)"
	@echo "  make lint            Ruff lint"
	@echo "  make fmt             Ruff format"
	@echo "  make test            Run tests"

venv:
	$(PY) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install --editable ".[dev]"

up:
	docker compose up -d

down:
	docker compose down

pull-models:
	docker compose exec -T ollama ollama pull $${OLLAMA_CHAT_MODEL:-llama3.2:1b}
	docker compose exec -T ollama ollama pull $${OLLAMA_EMBED_MODEL:-nomic-embed-text}

dev:
	set -a; [ -f .env ] && source .env; set +a; $(UVICORN) apps.api.main:app --reload --host 0.0.0.0 --port 8000

ingest:
	$(COPILOT) ingest docs

ask:
	@if [ -z "$(Q)" ]; then echo "Usage: make ask Q='your question' [C=1]"; exit 1; fi
	@if [ "$(C)" = "1" ]; then $(COPILOT) ask "$(Q)" --citations; else $(COPILOT) ask "$(Q)"; fi

kpi:
	@if [ -z "$(WEEK)" ]; then echo "Usage: make kpi WEEK=YYYY-MM-DD [BY=campaign] [DATA=data]"; exit 1; fi
	$(COPILOT) kpi --week "$(WEEK)" --by "$${BY:-campaign}" --data-dir "$${DATA:-data}"

investigate:
	@if [ -z "$(WEEK)" ]; then echo "Usage: make investigate WEEK=YYYY-MM-DD Q='...' [BY=campaign] [N=5] [DATA=data]"; exit 1; fi
	@if [ -z "$(Q)" ]; then echo "Usage: make investigate WEEK=YYYY-MM-DD Q='...' [BY=campaign] [N=5] [DATA=data]"; exit 1; fi
	$(COPILOT) investigate "$(Q)" --week "$(WEEK)" --by "$${BY:-campaign}" --n "$${N:-5}" --data-dir "$${DATA:-data}"


gen-data:
	$(PY) scripts/generate_mock_data.py

lint:
	$(RUFF) check .

fmt:
	$(RUFF) format .

test:
	set -a; [ -f .env ] && source .env; set +a; $(PYTEST)

.PHONY: help venv up down pull-models dev ingest ask lint fmt test kpi investigate gen-data

eval:
	$(VENV)/bin/python scripts/eval.py

.PHONY: eval