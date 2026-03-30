#!/usr/bin/env bash
set -euo pipefail

echo "==> Health"
curl -fsS http://localhost:8000/health
echo

echo "==> Generate data"
python scripts/generate_mock_data.py

echo "==> Ingest docs"
copilot ingest docs/

echo "==> Ask (RAG)"
copilot ask "What UTMs are required and what formatting rules do we follow?" --citations

echo "==> Investigate (LLM + tools)"
copilot investigate "Why did CAC rise last week? Identify the worst campaigns." --week 2026-03-16