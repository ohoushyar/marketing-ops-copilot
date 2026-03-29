from __future__ import annotations
import pandas as pd
from .io import DataBundle


def _safe_div(n: pd.Series, d: pd.Series) -> pd.Series:
    return n.div(d.where(d != 0))


def daily_kpis(bundle: DataBundle) -> pd.DataFrame:
    df = (
        bundle.spend.merge(bundle.clicks, on=["date", "campaign"], how="left")
        .merge(bundle.conversions, on=["date", "campaign"], how="left")
        .fillna({"clicks": 0, "impressions": 0, "conversions": 0, "revenue": 0.0})
    )

    df["ctr"] = _safe_div(df["clicks"], df["impressions"])
    df["cpc"] = _safe_div(df["spend"], df["clicks"])
    df["cvr"] = _safe_div(df["conversions"], df["clicks"])
    df["cac"] = _safe_div(df["spend"], df["conversions"])
    df["roas"] = _safe_div(df["revenue"], df["spend"])

    return df


def weekly_aggregate(df_daily: pd.DataFrame, week_start: str, by: list[str]) -> pd.DataFrame:
    start = pd.Timestamp(week_start)
    end = start + pd.Timedelta(days=6)

    dfw = df_daily[(df_daily["date"] >= start) & (df_daily["date"] <= end)].copy()

    group_cols = by
    agg = dfw.groupby(group_cols, as_index=False).agg(
        spend=("spend", "sum"),
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )

    agg["ctr"] = agg["clicks"] / agg["impressions"].where(agg["impressions"] != 0)
    agg["cpc"] = agg["spend"] / agg["clicks"].where(agg["clicks"] != 0)
    agg["cvr"] = agg["conversions"] / agg["clicks"].where(agg["clicks"] != 0)
    agg["cac"] = agg["spend"] / agg["conversions"].where(agg["conversions"] != 0)
    agg["roas"] = agg["revenue"] / agg["spend"].where(agg["spend"] != 0)

    return agg
