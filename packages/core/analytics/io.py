from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

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

    # basic type normalization
    spend["campaign"] = spend["campaign"].astype(str)
    clicks["campaign"] = clicks["campaign"].astype(str)
    conv["campaign"] = conv["campaign"].astype(str)

    return DataBundle(spend=spend, clicks=clicks, conversions=conv)