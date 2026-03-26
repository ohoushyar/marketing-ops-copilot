from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from packages.core.ollama import chat
from packages.core.analytics.tools import Plan
from packages.core.analytics.io import load_data
from packages.core.analytics.kpis import daily_kpis, weekly_aggregate
from packages.core.analytics.compare import kpi_delta as kpi_delta_fn, top_movers as top_movers_fn

PLANNER_SYSTEM = """You are an analytics planner for marketing performance investigations.
You must output ONLY valid JSON.
Choose a minimal set of tool calls to answer the question.
Available tools:
- weekly_kpis(week_start, by)
- kpi_delta(week_a_start, week_b_start, by)
- top_movers(week_a_start, week_b_start, by, kpi, n, direction)

Rules:
- Always include kpi_delta for week-over-week questions.
- Use top_movers when asked "why" something changed.
- Prefer by=["campaign"] unless user asks otherwise.
Output schema:
{"calls":[ ... tool call objects ... ]}
"""

NARRATOR_SYSTEM = """You are a marketing analytics assistant.
Use ONLY the provided tool results for any numbers.
If a number is not in the tool results, do not invent it.
Provide:
- concise diagnosis (drivers)
- what to check next (actions)
"""

def _exec_tools(plan: Plan, data_dir: str) -> list[dict]:
    bundle = load_data(data_dir)
    df_daily = daily_kpis(bundle)

    tool_runs: list[dict] = []

    for call in plan.calls:
        if call.tool == "weekly_kpis":
            df = weekly_aggregate(df_daily, week_start=call.week_start, by=call.by)
            tool_runs.append({"tool": call.tool, "input": call.model_dump(), "rows": df.to_dict(orient="records")})

        elif call.tool == "kpi_delta":
            a = weekly_aggregate(df_daily, week_start=call.week_a_start, by=call.by)
            b = weekly_aggregate(df_daily, week_start=call.week_b_start, by=call.by)
            df = kpi_delta_fn(a, b, by=call.by)
            tool_runs.append({"tool": call.tool, "input": call.model_dump(), "rows": df.to_dict(orient="records")})

        elif call.tool == "top_movers":
            a = weekly_aggregate(df_daily, week_start=call.week_a_start, by=call.by)
            b = weekly_aggregate(df_daily, week_start=call.week_b_start, by=call.by)
            delta = kpi_delta_fn(a, b, by=call.by)

            if call.kpi == "cac":
                ascending = True if call.direction == "improved" else False
            else:
                ascending = False if call.direction == "improved" else True

            df = top_movers_fn(delta, kpi=call.kpi, n=call.n, ascending=ascending)
            tool_runs.append({"tool": call.tool, "input": call.model_dump(), "rows": df.to_dict(orient="records")})

    return tool_runs

async def investigate(question: str, week_start: str, data_dir: str = "data") -> dict:
    # Planner
    user = json.dumps(
        {
            "question": question,
            "week_start": week_start,
            "default_previous_week_start": "week_start_minus_7_days",
        }
    )
    plan_text = await chat(PLANNER_SYSTEM, user)

    try:
        plan = Plan.model_validate_json(plan_text)
    except ValidationError as e:
        # fallback: deterministic minimal plan
        # (you can improve this later: attempt to extract JSON substring)
        plan = Plan(
            calls=[
                {"tool": "kpi_delta", "week_a_start": week_start, "week_b_start": week_start, "by": ["campaign"]}
            ]
        )

    tool_runs = _exec_tools(plan, data_dir=data_dir)

    # Narrator
    narrator_user = json.dumps({"question": question, "tool_runs": tool_runs})
    answer_text = await chat(NARRATOR_SYSTEM, narrator_user)

    return {"answer": answer_text, "plan": plan.model_dump(), "tool_runs": tool_runs}