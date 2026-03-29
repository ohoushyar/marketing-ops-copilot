from __future__ import annotations
from typing import Literal, Union
from pydantic import BaseModel, Field


class WeeklyKpisCall(BaseModel):
    tool: Literal["weekly_kpis"]
    week_start: str
    by: list[str] = Field(default_factory=lambda: ["campaign"])


class KpiDeltaCall(BaseModel):
    tool: Literal["kpi_delta"]
    week_a_start: str
    week_b_start: str
    by: list[str] = Field(default_factory=lambda: ["campaign"])


class TopMoversCall(BaseModel):
    tool: Literal["top_movers"]
    week_a_start: str
    week_b_start: str
    by: list[str] = Field(default_factory=lambda: ["campaign"])
    kpi: Literal["cac", "conversions", "roas", "cvr", "ctr", "spend"] = "cac"
    n: int = 5
    direction: Literal["worsened", "improved"] = "worsened"


ToolCall = Union[WeeklyKpisCall, KpiDeltaCall, TopMoversCall]


class Plan(BaseModel):
    calls: list[ToolCall]
