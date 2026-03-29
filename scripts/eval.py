from __future__ import annotations

import json
from pathlib import Path
import sys
import os
import httpx

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

def post(path: str, payload: dict, timeout: float = 300.0) -> dict:
    r = httpx.post(f"{API_BASE_URL}{path}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def load_cases(path: str) -> list[dict]:
    cases = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        cases.append(json.loads(line))
    return cases

def is_refusal(ans: str) -> bool:
    s = ans.lower()
    return "i don't have enough information" in s or "i don't know" in s

def main() -> int:
    cases = load_cases("evals/golden.jsonl")

    total = 0
    passed = 0

    rag_total = rag_pass = 0
    ana_total = ana_pass = 0

    for c in cases:
        total += 1
        kind = c["kind"]
        ok = False

        try:
            if kind == "rag":
                rag_total += 1
                resp = post("/chat", {"question": c["question"], "citations": True})
                ans = resp.get("answer", "")
                citations = resp.get("citations", [])

                if c.get("expect_refusal"):
                    ok = is_refusal(ans) and len(citations) == 0
                    if not ok:
                        print(f"  Expected refusal but got: {ans[:100]}")
                else:
                    must = set(c.get("must_cite", []))
                    got = set(ci.get("source_path") for ci in citations)
                    ok = len(must & got) > 0
                    if not ok:
                        print(f"  Expected citations: {must}")
                        print(f"  Got citations: {got}")

                if ok:
                    rag_pass += 1

            elif kind == "analytics":
                ana_total += 1
                # Prefer Day 4 endpoint if you have it; else swap to /analytics/kpi_delta.
                resp = post(
                    "/analytics/investigate",
                    {
                        "question": c["question"],
                        "week_start": c["week_start"],
                        "data_dir": c.get("data_dir", "data"),
                    },
                    timeout=60.0,
                )
                tool_runs = resp.get("tool_runs", [])
                ans = resp.get("answer", "")

                has_rows = any(tr.get("rows") for tr in tool_runs)
                # cheap grounding: answer mentions a campaign found in tool output
                campaigns = set()
                for tr in tool_runs:
                    for row in tr.get("rows", []):
                        if "campaign" in row:
                            campaigns.add(str(row["campaign"]))

                mentions_campaign = any((camp in ans) for camp in list(campaigns)[:20]) if campaigns else False
                ok = has_rows and (mentions_campaign or len(campaigns) == 0)
                
                if not ok:
                    print(f"  Answer: {ans[:150]}")
                    print(f"  Has rows: {has_rows}, Campaigns: {list(campaigns)[:5]}, Mentions: {mentions_campaign}")

                if ok:
                    ana_pass += 1

        except Exception as e:
            ok = False

        passed += int(ok)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {c.get('id','(no id)')} [{kind}]")

    print("\nSummary")
    print(f"Total: {passed}/{total}")
    if rag_total:
        print(f"RAG: {rag_pass}/{rag_total}")
    if ana_total:
        print(f"Analytics: {ana_pass}/{ana_total}")

    return 0 if passed == total else 1

if __name__ == "__main__":
    raise SystemExit(main())