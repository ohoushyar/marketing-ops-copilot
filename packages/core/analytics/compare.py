from __future__ import annotations
import pandas as pd


def kpi_delta(df_a: pd.DataFrame, df_b: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    key = by
    merged = df_a.merge(df_b, on=key, how="outer", suffixes=("_a", "_b")).fillna(0)

    for col in [
        "spend",
        "clicks",
        "impressions",
        "conversions",
        "revenue",
        "ctr",
        "cpc",
        "cvr",
        "cac",
        "roas",
    ]:
        if f"{col}_a" not in merged or f"{col}_b" not in merged:
            continue
        merged[f"{col}_delta"] = merged[f"{col}_b"] - merged[f"{col}_a"]
        merged[f"{col}_pct"] = merged[f"{col}_delta"] / merged[f"{col}_a"].where(
            merged[f"{col}_a"] != 0
        )

    return merged


def top_movers(delta: pd.DataFrame, kpi: str, n: int = 10, ascending: bool = False) -> pd.DataFrame:
    # for CAC: ascending=True is "improved"; descending is "worsened"
    col = f"{kpi}_pct"
    if col not in delta.columns:
        raise ValueError(f"Missing {col}")
    return delta.sort_values(col, ascending=ascending).head(n)
