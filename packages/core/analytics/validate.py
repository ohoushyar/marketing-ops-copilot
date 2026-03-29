from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaSpec:
    name: str
    required_cols: set[str]


SPEND_SPEC = SchemaSpec("spend.csv", {"date", "campaign", "spend"})
CLICKS_SPEC = SchemaSpec("clicks.csv", {"date", "campaign", "clicks", "impressions"})
CONV_SPEC = SchemaSpec("conversions.csv", {"date", "campaign", "conversions", "revenue"})


def validate_df_cols(df, spec: SchemaSpec) -> None:
    missing = spec.required_cols - set(df.columns)
    if missing:
        raise ValueError(f"{spec.name} missing required columns: {sorted(missing)}")


ALLOWED_GROUP_BY = {"campaign", "channel"}
