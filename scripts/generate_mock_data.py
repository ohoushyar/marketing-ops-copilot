from __future__ import annotations
import random
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

random.seed(7)


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


campaigns = [
    "2026q1-demandgen-widget-us-prospecting-v1",
    "2026q1-demandgen-widget-us-prospecting-v2",
    "2026q1-brand-widget-us-high_intent-v1",
    "2026q1-retargeting-widget-us-customer-v1",
    "2026q1-demandgen-widget-emea-prospecting-v1",
]

channels = {
    campaigns[0]: "meta",
    campaigns[1]: "meta",
    campaigns[2]: "google",
    campaigns[3]: "meta",
    campaigns[4]: "linkedin",
}

start = date(2026, 2, 10)
end = date(2026, 3, 22)

rows_spend = []
rows_clicks = []
rows_conv = []

for d in daterange(start, end):
    for c in campaigns:
        base_spend = {"google": 700, "meta": 500, "linkedin": 350}[channels[c]]
        noise = random.uniform(0.8, 1.2)
        spend = base_spend * noise

        impressions = int(spend * random.uniform(80, 140))
        ctr = random.uniform(0.006, 0.02)
        clicks = max(1, int(impressions * ctr))

        # induce a "CAC rose last week" event for one campaign in the last 7 days
        recent = d >= date(2026, 3, 16)
        bad_campaign = c == campaigns[0] and recent
        cvr = random.uniform(0.02, 0.06) * (0.6 if bad_campaign else 1.0)
        conversions = max(0, int(clicks * cvr))

        revenue = conversions * random.uniform(60, 140)

        rows_spend.append(
            {"date": d.isoformat(), "channel": channels[c], "campaign": c, "spend": round(spend, 2)}
        )
        rows_clicks.append(
            {"date": d.isoformat(), "campaign": c, "clicks": clicks, "impressions": impressions}
        )
        rows_conv.append(
            {
                "date": d.isoformat(),
                "campaign": c,
                "conversions": conversions,
                "revenue": round(revenue, 2),
            }
        )

out = Path("data")
out.mkdir(parents=True, exist_ok=True)

pd.DataFrame(rows_spend).to_csv(out / "spend.csv", index=False)
pd.DataFrame(rows_clicks).to_csv(out / "clicks.csv", index=False)
pd.DataFrame(rows_conv).to_csv(out / "conversions.csv", index=False)

print("Wrote data/spend.csv, data/clicks.csv, data/conversions.csv")
