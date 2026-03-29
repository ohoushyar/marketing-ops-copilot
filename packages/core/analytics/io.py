from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

from .validate import validate_df_cols, SPEND_SPEC, CLICKS_SPEC, CONV_SPEC


@dataclass(frozen=True)
class DataBundle:
    spend: pd.DataFrame
    clicks: pd.DataFrame
    conversions: pd.DataFrame


def load_data(data_dir: str = "data") -> DataBundle:
    root = Path(data_dir)

    spend = pd.read_csv(root / "spend.csv", parse_dates=["date"])
    clicks = pd.read_csv(root / "clicks.csv", parse_dates=["date"])
    conv = pd.read_csv(root / "conversions.csv", parse_dates=["date"])

    validate_df_cols(spend, SPEND_SPEC)
    validate_df_cols(clicks, CLICKS_SPEC)
    validate_df_cols(conv, CONV_SPEC)

    for df in (spend, clicks, conv):
        df["campaign"] = df["campaign"].astype(str)

    return DataBundle(spend=spend, clicks=clicks, conversions=conv)
